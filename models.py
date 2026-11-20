from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class register(Base):

    __tablename__="robot_register"
    robot_id=Column(String,primary_key=True,unique=True)
    Model=Column(String, nullable=False)
    Type=Column(String, nullable=False)
    Location=Column(String, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

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

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)

class AlertModel(Base):
    __tablename__="alerts"
    id=Column(Integer,primary_key=True,index=True)
    robot_id=Column(String,ForeignKey("robot_register.robot_id"),nullable=False) #from the table register
    metric=Column(String,nullable=False)
    value=Column(Float,nullable=False)
    severity=Column(String ,nullable=False)
    message=Column(String,nullable=False)
    resolved=Column(Boolean,default=False)#remains false until solved
    problem_created=Column(DateTime,default=datetime.now) #Time at which problem was created

