from sqlalchemy import Column, Integer, String,Date
from database.database import Base

class User(Base):
    __tablename__ = "users"
    user_id    = Column(String(45), primary_key=True, index=True)
    user_name  = Column(String(45), index=True)        # 길이 지정
    user_email = Column(String(100), unique=True, index=True)  # 길이 지정
    user_pw    = Column(String(255))   # 비밀번호 해시는 길게 잡는 게 안전
    birthday   = Column(Date)

    class Config:
        orm_mode = True