from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
from models import RobotSensorModel,register
import schemas

from schemas import RobotSensor,RobotRegister
from database import engine,get_db


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

# 1. Register a robot
@app.post("/robots/register")
def register_robot(
    data: RobotRegister,
    session: Session = Depends(get_db)
):
    robot = session.query(register).filter(
        register.robot_id == data.robot_id
    ).first()

    if robot:
        raise HTTPException(
            status_code=409,
            detail="Robot already exists"
        )

    new_robot = register(
        robot_id=data.robot_id,
        Model=data.Model,
        Type=data.Type,
        Location=data.Location
    )

    session.add(new_robot)
    session.commit()
    session.refresh(new_robot)

    return {
        "message": "Robot registered successfully",
        "robot_id": new_robot.robot_id
    }


# 2. Get a specific robot by ID

@app.get("/robots/{robot_id}")
def get_robot(
    robot_id: str,
    session: Session = Depends(get_db)
):
    robot = session.query(register).filter(
        register.robot_id == robot_id
    ).first()

    if not robot:
        raise HTTPException(
            status_code=404,
            detail="Robot not registered"
        )

    return {
        "robot_id": robot.robot_id,
        "Model": robot.Model,
        "Type": robot.Type,
        "Location": robot.Location
    }

# 3. Receive sensor data
@app.post("/robots/{robot_id}/sensor-data")
async def receive_sensor_data(
    robot_id:str,
    sensor: RobotSensor,session:Session=Depends(get_db)
):
        # 1. Check whether the robot is registered
    robot = session.query(register).filter(
        register.robot_id == robot_id
    ).first()

    if not robot:
        raise HTTPException(
            status_code=404,
            detail="Robot ID not registered"
        )

    # 2. Ensure the submitted ID matches the URL ID
    if sensor.robot_id != robot_id:
        raise HTTPException(
            status_code=400,
            detail="Robot ID mismatch"
        )

    sensor_reading=RobotSensorModel(
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

    return {"message":f"Sensor readings of {sensor_reading.robot_id} is stored successfully"}

# 4. Retrieve sensor data
@app.get(
    "/robots/{robot_id}/sensor-data",
    response_model=list[schemas.RobotSensorResponse]
)
def get_sensor_data(robot_id: str, session: Session = Depends(get_db)):
    robot = session.query(register).filter(
        register.robot_id == robot_id
    ).first()

    if not robot:
        raise HTTPException(status_code=404, detail="Robot does not exist")

    readings = session.query(RobotSensorModel).filter(
        RobotSensorModel.robot_id == robot_id
    ).all()

    return readings