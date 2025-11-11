from database.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    db: Session = SessionLocal()  # 세션 생성
    try:
        yield db  # 의존성 주입
    finally:
        db.close()  # 요청 끝나면 세션 닫음
