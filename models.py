from sqlalchemy import Column, Integer, String, Float,DateTime
from database import Base
from datetime import datetime

class register(Base):

    __tablename__="robot_register"
    robot_id=Column(String,primary_key=True,unique=True)
    Model=Column(String, nullable=False)
    Type=Column(String, nullable=False)
    Location=Column(String, nullable=False)

class RobotSensorModel(Base):
    __tablename__ = "robot_sensors"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String, index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    current_draw = Column(Float, nullable=False)
    proximity = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)