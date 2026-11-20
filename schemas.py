from pydantic import BaseModel,ConfigDict,EmailStr
from datetime import datetime
# This is send to the server


class RobotRegister(BaseModel):
    robot_id: str
    Model: str
    Type: str
    Location: str
class RobotSensor(BaseModel):
    robot_id:str
    temperature:float
    vibration:float
    current_draw:float
    proximity:float
    status:str
#This is what shown when reading the data
class RobotSensorResponse(RobotSensor):
    id:int
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    disabled: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class AlertResponse(BaseModel):
    id: int
    robot_id: str
    metric: str
    value : float
    severity: str
    message :str
    problem_created: datetime
    resolved :bool
    model_config=ConfigDict(from_attributes=True)

class RobotCommand(BaseModel):
    command:str
    reason :str | None =None

