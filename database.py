from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
SQLALCHEMY_DATABASE_URL="sqlite:///./sql_app.db"

#create engine to establish actual DB connection
engine= create_engine(
    SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread":False}
)
# Each instance of SessionLocal will be a database session
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
#Base class from which our database models will inherit from
Base=declarative_base()

#Dependency to yiled database sessions per request,ensuring to close properly
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


