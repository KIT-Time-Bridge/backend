from pydantic import BaseModel
from datetime import date

class PostCreate(BaseModel):
    type:str #1=보호자 2=실종자 본인
    session_id:str
    photo_age:int
    missing_birth:date
    missing_date:date
    missing_name:str
    missing_situation:str
    missing_extra_evidence:str
    missing_place:str
    gender:str

class UserCreate(BaseModel):
    name:str
    email:str
    password:str
    username:str
    birth:date