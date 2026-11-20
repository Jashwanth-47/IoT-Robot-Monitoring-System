from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List,Dict
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import jwt
from pwdlib import PasswordHash
from fastapi import WebSocket,WebSocketDisconnect
import models
from models import RobotSensorModel, register,AlertModel
import schemas
from database import engine, get_db
import json
from typing import Dict, List
from fastapi import WebSocket

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    raise RuntimeError("Set SECRET_KEY in your .env file")

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)




class ConnectionManager:
    def __init__(self):
        # Maps robot_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, robot_id: str, websocket: WebSocket):
        await websocket.accept()
        if robot_id not in self.active_connections:
            self.active_connections[robot_id] = []
        self.active_connections[robot_id].append(websocket)

    def disconnect(self, robot_id: str, websocket: WebSocket):
        """Safely removes a disconnected websocket from the pool."""
        if robot_id in self.active_connections:
            if websocket in self.active_connections[robot_id]:
                self.active_connections[robot_id].remove(websocket)
            # Clean up the key if no clients are left listening to this robot
            if len(self.active_connections[robot_id]) == 0:
                del self.active_connections[robot_id]

    async def broadcast(self, robot_id: str, message: dict):
        """Broadcasts JSON payload to all active clients of a robot."""
        if robot_id not in self.active_connections:
            return

        dead_connections = []
        # Copy the list so iteration is safe even if connections close
        for connection in list(self.active_connections[robot_id]):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up any dead connections caught during broadcast
        for dead_ws in dead_connections:
            self.disconnect(robot_id, dead_ws)

manager = ConnectionManager()

# ================= AUTH HELPERS & DEPENDENCIES =================

def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expires_at
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="User doesn't exist")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = session.query(models.UserModel).filter(models.UserModel.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if user.disabled:
        raise HTTPException(status_code=403, detail="User account is disabled")
    return user

# ================= AUTH ENDPOINTS =================
@app.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    data: schemas.UserCreate, 
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    if current_user.username != "Jashwanth":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only administrators can register new operators."
        )

    existing_user = session.query(models.UserModel).filter(
        (models.UserModel.username == data.username) |
        (models.UserModel.email == str(data.email))
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")

    new_user = models.UserModel(
        username=data.username,
        email=str(data.email),
        full_name=data.full_name,
        hashed_password=password_hash.hash(data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login_user(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    user = session.query(models.UserModel).filter(
        models.UserModel.username == form.username
    ).first()

    if not user or not password_hash.verify(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    token = create_access_token(user.username)
    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ================= ROBOT & SENSOR ENDPOINTS =================

@app.post("/robots/register")
def register_robot(
    data: schemas.RobotRegister,
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    robot = session.query(register).filter(
        register.robot_id == data.robot_id
    ).first()

    if robot:
        raise HTTPException(status_code=409, detail="Robot already exists")

    new_robot = register(
        robot_id=data.robot_id,
        Model=data.Model,
        Type=data.Type,
        Location=data.Location,
        owner_id=current_user.id
    )

    session.add(new_robot)
    session.commit()
    session.refresh(new_robot)

    return {
        "message": "Robot registered successfully",
        "robot_id": new_robot.robot_id,
        "owner": current_user.username
    }

@app.get("/robots")
def list_user_robots(
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    user_robots = session.query(register).filter(
        register.owner_id == current_user.id
    ).all()
    return user_robots

@app.get("/robots/{robot_id}")
def get_robot(
    robot_id: str,
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    robot = session.query(register).filter(
        register.robot_id == robot_id,
        register.owner_id == current_user.id
    ).first()

    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found or access denied")

    return {
        "robot_id": robot.robot_id,
        "Model": robot.Model,
        "Type": robot.Type,
        "Location": robot.Location
    }

@app.post("/robots/{robot_id}/sensor-data")
async def receive_sensor_data(
    robot_id: str,
    sensor: schemas.RobotSensor,
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    robot = session.query(register).filter(
        register.robot_id == robot_id
    ).first()

    if not robot:
        raise HTTPException(status_code=404, detail="Robot ID not registered")

    if sensor.robot_id != robot_id:
        raise HTTPException(status_code=400, detail="Robot ID mismatch")

    sensor_reading = RobotSensorModel(
        robot_id=sensor.robot_id,
        temperature=sensor.temperature,
        vibration=sensor.vibration,
        current_draw=sensor.current_draw,
        proximity=sensor.proximity,
        status=sensor.status,
    )
    session.add(sensor_reading)
    session.commit()
    session.refresh(sensor_reading)
    generated_alerts=[]
    #Check temperature
    if sensor.temperature>=85.0:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="temperature",
            value=sensor_reading.temperature,
            severity="CRITICAL",
            message="Critical Overheat :Temperature exceeded 85°C"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    elif sensor.temperature>=75.0 and sensor.temperature<85.0:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="temperature",
            value=sensor_reading.temperature,
            severity="WARNING",
            message="High temperature warning"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    elif sensor.temperature<0.0:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="temperature",
            value=sensor_reading.temperature,
            severity="WARNING",
            message="Sub-zero or sensor reading fault"
        )
        session.add(new_alert)    
        
        generated_alerts.append(new_alert)
        session.commit()
    #Check Vibration
    if sensor.vibration >4.5:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="Vibration",
            value=sensor_reading.vibration,
            severity="CRITICAL",
            message="Severe vibration (Zone D): Mechanical failure risk"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    elif sensor.vibration >=2.8 and sensor.vibration <4.5:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="Vibration",
            value=sensor_reading.vibration,
            severity="WARNING",
            message="Elevated vibration (Zone C): Mechanical wear warning"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    #Check Current Draw
    if sensor.current_draw >=15.0:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="current_draw",
            value=sensor_reading.current_draw,
            severity="CRITICAL",
            message="Motor stall or short-circuit detected"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    elif sensor.current_draw >=12.0 and sensor.current_draw <15.0:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="current_draw",
            value=sensor_reading.current_draw,
            severity="WARNING",
            message="High electrical load on drive system"
        )
        session.add(new_alert)
        
        generated_alerts.append(new_alert)
        session.commit()
    #Check proximitty
    if sensor.proximity <=0.2:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="proximity",
            value=sensor_reading.proximity,
            severity="CRITICAL",
            message="Immediate Collision Risk: Obstacle within 0.2m critical zone"
        )
        session.add(new_alert)
        generated_alerts.append(new_alert)
        session.commit()
    elif sensor.proximity <=0.5 and sensor.proximity >0.2:
        new_alert=AlertModel(
            robot_id=robot_id,
            metric="proximity",
            value=sensor_reading.proximity,
            severity="WARNING",
            message="Proximity Warning: Object detected within 0.5m buffer zone"
        )
        session.add(new_alert)               
        generated_alerts.append(new_alert)
        session.commit()


    #converting saved record into a plain dictionary
    telemetry_payload = {
    "robot_id": robot_id,
    "temperature": sensor_reading.temperature,
    "vibration": sensor_reading.vibration,
    "current_draw": sensor_reading.current_draw,
    "proximity": sensor_reading.proximity,
    "status": sensor_reading.status,
    "created_at": str(sensor_reading.created_at)
    }
    await manager.broadcast(robot_id,telemetry_payload)
    # Instant push for every detected alert
    for alert in generated_alerts:
        alert_payload={
            "type":"Incident_Alert",
            "alert_id":alert.id,
            "robot_id":robot_id,
            "metric":alert.metric,
            "value":alert.value,
            "severity":alert.severity,
            "messsage":alert.message,
            "timestamp":str(alert.problem_created)
        }
        await manager.broadcast(robot_id,alert_payload)
    return sensor_reading

@app.get(
    
    "/robots/{robot_id}/sensor-data",
    response_model=list[schemas.RobotSensorResponse]
)
def get_sensor_data(
    robot_id: str,
    limit: int = 10,
    session: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    robot = session.query(register).filter(
        register.robot_id == robot_id,
        register.owner_id == current_user.id
    ).first()

    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found or access denied")

    readings = (
        session.query(RobotSensorModel)
        .filter(RobotSensorModel.robot_id == robot_id)
        .order_by(RobotSensorModel.created_at.desc())
        .limit(limit)
        .all()
    )

    return readings
@app.get("/robots/{robot_id}/alerts",response_model=list[schemas.AlertResponse])
def get_robot_alerts(
    robot_id:str,
    session:Session=Depends(get_db),
    current_user:models.UserModel=Depends(get_current_user)
):
    alerts=(
        session.query(AlertModel).filter(AlertModel.robot_id==robot_id).order_by(AlertModel.problem_created.desc()).all()
    )
    return alerts
@app.patch("/alerts/{alert_id}/resolve")
def patch_resolving(alert_id :int ,session:Session=Depends(get_db),current_user:models.UserModel=Depends(get_current_user)):
    alert=session.query(AlertModel).filter(AlertModel.id==alert_id).first()
    if not alert:
        raise HTTPException(status_code=404,detail="Alert incident not found")
    alert.resolved=True
    session.commit()
    return {
        "message": f"Alert {alert_id} marked as resolved",
        "alert_id": alert_id,
        "resolved": True
    } 
@app.websocket("/ws/robots/{robot_id}")
async def websocket_endpoint(websocket: WebSocket, robot_id: str):
    await manager.connect(robot_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(robot_id, websocket)
        await manager.broadcast(robot_id, {
            "type": "SYSTEM",
            "message": f"Client disconnected from {robot_id}"
        })
@app.post("/robots/{robot_id}/command")
async def command(robot_id:str, cmd:schemas.RobotCommand,session:Session=Depends(get_db),current_user: models.UserModel=Depends(get_current_user)):
    robot=session.query(register).filter(register.robot_id==robot_id).first()
    if not robot:
        raise HTTPException(status_code=404,detail="Robot not found")
    
    command_payload={
        "type":"Command",
        "robot_id":robot_id,
        "action":cmd.command,
        "reason":cmd.reason,
        "issued_by":current_user.username
    }
    await manager.broadcast(robot_id, json.dumps(command_payload))
    return {
        "status": "COMMAND_DISPATCHED",
        "robot_id": robot_id,
        "action": cmd.command,
        "issued_by": current_user.username
    }