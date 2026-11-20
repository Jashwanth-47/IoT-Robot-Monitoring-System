from datetime import datetime,timedelta,timezone
from typing import Annotated

import jwt
from fastapi import Depends,FastAPI,HTTPException,status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
class Token (BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None=None

class User(BaseModel):
    username:str
    email:str |None=None
    full_name:str|None=None
    disabled:bool |None=None

class UserInDB(User):
    hashed_password: str

