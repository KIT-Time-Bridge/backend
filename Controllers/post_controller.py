from sqlalchemy.orm import Session
from fastapi import HTTPException
from services.session_service import SessionManager
from datetime import date
from services.post_service import PostService
from typing import Optional
from fastapi import UploadFile

class PostController:
    async def img_aging(self, missing_birth,img):
        post_service=PostService()
        return await post_service.img_aging(missing_birth, img)
    async def post_upload(
        self,
        session_id: str,
        type: int,
        missing_name: str,
        gender: str,
        missing_birth: date,
        db: Session,

        img_origin: Optional[UploadFile] = None,
        img_aging: Optional[UploadFile] = None,
        missing_date: Optional[date] = None,
        missing_situation: Optional[str] = None,
        missing_extra_evidence: Optional[str] = None,
        missing_place: Optional[str] = None,
        photo_age: Optional[int] = None,
    ):
        post_service = PostService()

        # 세션 ID로 user_id 찾기
        session_manager = SessionManager()
        user_id = session_manager.get_user(session_id)

        # 서비스 계층 호출 (UploadFile 그대로 넘김)
        return await post_service.post_upload(
            user_id=user_id,
            type=type,
            missing_name=missing_name,
            gender=gender,
            missing_birth=missing_birth,
            db=db,
            img_origin=img_origin,
            img_aging=img_aging,
            missing_date=missing_date,
            missing_situation=missing_situation,
            missing_extra_evidence=missing_extra_evidence,
            missing_place=missing_place,
            photo_age=photo_age,
        )
    def register_missing_search(self, session_id, db:Session):
        session_manager=SessionManager()
        post_service=PostService()
        user_id=session_manager.get_user(session_id)
        return post_service.register_missing_search(user_id, db)
    
    def all_missing_search_by_family(self, pageNum:int, db:Session, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None):
        post_service=PostService()
        return post_service.all_missing_search_by_family(pageNum, db, search_keywords, gender_id, missing_birth, missing_date, missing_place)
    
    def all_missing_search_by_missing(self, pageNum:int, db:Session, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None):
        post_service=PostService()
        return post_service.all_missing_search_by_missing(pageNum, db, search_keywords, gender_id, missing_birth, missing_date, missing_place)
    
    def detail_missing_search(self, db:Session, missing_id):
        post_service=PostService()
        return post_service.detail_missing_search(db,missing_id)
    async def delete_missing(self, db:Session, missing_id):
        post_service=PostService()
        return await post_service.delete_post(db,missing_id)
    
    async def update_post(
        self,
        db: Session,
        missing_id: str,                         # ✅ 필수
        type: Optional[int] = None,
        missing_name: Optional[str] = None,
        gender: Optional[str] = None,
        missing_birth: Optional[date] = None,
        img_origin=None,
        img_aging=None,
        missing_date: Optional[date] = None,
        missing_situation: Optional[str] = None,
        missing_extra_evidence: Optional[str] = None,
        missing_place: Optional[str] = None,
        photo_age: Optional[int] = None,
    ):
        post_service = PostService()

        # 서비스 호출 (await 필요)
        return await post_service.post_update(
            db=db,
            missing_id=missing_id,
            type=type,
            missing_name=missing_name,
            gender=gender,
            missing_birth=missing_birth,
            img_origin=img_origin,
            img_aging=img_aging,
            missing_date=missing_date,
            missing_situation=missing_situation,
            missing_extra_evidence=missing_extra_evidence,
            missing_place=missing_place,
            photo_age=photo_age,
        )
    async def image_similarity(self, missingId, db, session_id):
        service=PostService()
        session_manager=SessionManager()
        user_id=session_manager.get_user(session_id)
        return await service.image_similarity(missingId,db, user_id)
    
    async def text_similarity(self, missingId, db, session_id):
        service=PostService()
        session_manager=SessionManager()
        user_id=session_manager.get_user(session_id)
        return await service.text_similarity(missingId,db, user_id)
    
    def get_pending_posts(self, db: Session):
        """승인 대기 게시글 조회"""
        service = PostService()
        return service.get_pending_posts(db)
    
    def approve_post(self, db: Session, post_id: str):
        """게시글 승인"""
        service = PostService()
        return service.approve_post(db, post_id)
