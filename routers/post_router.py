# routers/post_router.py
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from typing import Optional
from datetime import date
from fastapi.responses import StreamingResponse
from io import BytesIO
import httpx
from Controllers.post_controller import PostController
from fastapi import Request

import shutil

# 게시글 관련 라우터를 정의하는 객체
router = APIRouter(prefix="/api/posts", tags=["Posts"])

# 업로드된 이미지가 저장될 디렉터리
UPLOAD_DIR = "uploads/posts"
# uploads/posts 폴더가 없으면 자동으로 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def create_post(
    type: int = Form(...),
    name: str = Form(...),

    img_origin: Optional[UploadFile] = File(None),
    img_aging: Optional[UploadFile] = File(None),

    request:Request=None,
    gender: str = Form(...),
    birth: date = Form(...),

    missingDate: Optional[date] = Form(None),
    missing_situation: Optional[str] = Form(None),
    missing_extra_evidence: Optional[str] = Form(None),
    missing_place: Optional[str] = Form(None),
    photo_age: Optional[int] = Form(None),

    db: Session = Depends(get_db)   # ✅ DB 세션 주입
):
    post_controller = PostController()
    return await post_controller.post_upload(
        img_origin=img_origin,
        img_aging=img_aging,
        type=type,
        session_id=request.session.get("session_id"),
        gender=gender,
        missing_birth=birth,
        missing_date=missingDate,
        missing_name=name,
        missing_situation=missing_situation,
        missing_extra_evidence=missing_extra_evidence,
        missing_place=missing_place,
        photo_age=photo_age,
        db=db   # ✅ Controller에 전달
    )

# POST /img_aging 엔드포인트 정의
@router.post("/img_aging")
async def img_aging(
    img: UploadFile = File(...),       # 업로드된 이미지 파일
    missing_birth: date = Form(...)   # 실종자의 생년월일
):
  post_controller=PostController()
  return await post_controller.img_aging(missing_birth, img)

@router.post("/register_missing_search")
def register_missing_search(request:Request, db: Session = Depends(get_db)):
     post_controller=PostController()
     session_id=request.session.get("session_id")
     return post_controller.register_missing_search(session_id, db)


@router.post("/all_missing_search_missing")
def all_missing_search_in_missing(pageNum:int, request:Request, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None, db: Session = Depends(get_db)):
    post_controller=PostController()
    return post_controller.all_missing_search_by_missing(pageNum, db, search_keywords, gender_id, missing_birth, missing_date, missing_place)

@router.post("/all_missing_search_family")
def all_missing_search_in_family(pageNum:int, request:Request, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None, db: Session = Depends(get_db)):
    post_controller=PostController()
    return post_controller.all_missing_search_by_family(pageNum, db, search_keywords, gender_id, missing_birth, missing_date, missing_place)

@router.post("/detail_missing_search")
def detail_missing_search(missing_id, db: Session = Depends(get_db)):
    post_controller=PostController()
    return post_controller.detail_missing_search(db, missing_id)

@router.post("/delete_post")
async def delete_post(missing_id,  db: Session = Depends(get_db)):
    post_controller=PostController()
    return await post_controller.delete_missing(db,missing_id)

@router.post("/update_post")   # ✅ 슬래시(/) 빠졌음! 꼭 붙여야 합니다
async def update_post(   
    missing_id: str = Form(...),              # ✅ 필수 (PK)
    type: Optional[int] = Form(None),
    missing_name: Optional[str] = Form(None),
    img_origin: Optional[UploadFile] = File(None),
    img_aging: Optional[UploadFile] = File(None),
    gender: Optional[str] = Form(None),
    missing_birth: Optional[date] = Form(None),
    missing_date: Optional[date] = Form(None),
    missing_situation: Optional[str] = Form(None),
    missing_extra_evidence: Optional[str] = Form(None),
    missing_place: Optional[str] = Form(None),
    photo_age: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    post_controller = PostController()
    return await post_controller.update_post(
        db=db,
        missing_id=missing_id,
        type=type,
        missing_name=missing_name,
        img_origin=img_origin,
        img_aging=img_aging,
        gender=gender,
        missing_birth=missing_birth,
        missing_date=missing_date,
        missing_situation=missing_situation,
        missing_extra_evidence=missing_extra_evidence,
        missing_place=missing_place,
        photo_age=photo_age,
    )
@router.post("/image_similarity")
async def get_image_similarity(missingId:str,request:Request, db: Session = Depends(get_db)):
    post_controller=PostController()
    session_id=request.session.get("session_id")
    return await post_controller.image_similarity(missingId, db, session_id )

@router.get("/test")
def test(req: int):
    return {"id": req, "message": "hello"}
    