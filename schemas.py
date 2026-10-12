from pydantic import BaseModel,ConfigDict,Field
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