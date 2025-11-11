from pydantic import BaseModel
from datetime import date

class UserCreate(BaseModel):
    name:str
    email:str
    password:str
    username:str
    birth:date
class UserDelete(BaseModel):
    session_id:str
class UserLogin(BaseModel):
    user_id: str
    user_pw: str
class UserLogout(BaseModel):
    session_id:str