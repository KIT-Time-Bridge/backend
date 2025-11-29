from sqlalchemy.orm import Session
from schemas.user_schema import UserCreate, UserDelete, UserLogin, UserLogout
from fastapi import HTTPException
from services.user_service import UserService
from services.session_service import SessionManager
from fastapi import Response
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request, HTTPException

import uuid

class UserController:

    # -----------------------
    # 회원가입
    # -----------------------
    def create_user(self, user: UserCreate, db: Session) -> bool:
        service = UserService()   # 매번 생성
        UserService.register_user(service,db,user)
        return True


    # -----------------------
    # 회원 삭제
    # -----------------------
    def delete_user(self, session_id:str, db: Session) -> bool:
        service = UserService()
        session_manager=SessionManager()
        user_id=session_manager.get_user(session_id)
        session_manager.delete_session(session_id)
        service.delete_user(db,user_id)
        
        return True

    # -----------------------
    # 로그인
    # -----------------------
    def login(self, user: UserLogin, db: Session, request:Request) -> str:
        service=UserService()
        session_manager = SessionManager()
        session_id=UserService.login(service,db,user.user_id,user.user_pw,session_manager)
        request.session["session_id"]=session_id


        return {"message": "로그인 성공"}

    # -----------------------
    # 로그아웃
    # -----------------------
    def logout(self, session_id) -> bool:
        session_manager=SessionManager()
        session_manager.delete_session(session_id)
        return True
    
    async def send_email(self, session_id, missing_id, text, db:Session):
        session_manager=SessionManager()
        service=UserService()
        user_id=session_manager.get_user(session_id)
        return await service.send_email(user_id, text, db, missing_id)
    
    def session_is_vaild(self, session_id):
        session_manager=SessionManager()
        return session_manager.is_valid(session_id)
    
    def check_is_admin(self, session_id: str, db: Session) -> bool:
        """관리자 여부 확인"""
        session_manager = SessionManager()
        user_id = session_manager.get_user(session_id)
        if not user_id:
            return False
        service = UserService()
        return service.check_is_admin(db, user_id)
    
    def get_current_user_id(self, session_id: str) -> str | None:
        """현재 로그인한 사용자 ID 반환"""
        session_manager = SessionManager()
        return session_manager.get_user(session_id)