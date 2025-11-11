from fastapi import FastAPI
from routers import user_router  # → 실제 라우터 경로에 맞게 수정
from database.database import Base, engine
from fastapi.staticfiles import StaticFiles
from routers import post_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(
    title="My API",
    docs_url="/api/docs",          # Swagger UI
    redoc_url="/api/redoc",        # Redoc 문서
    openapi_url="/api/openapi.json"  # OpenAPI 스펙
)
# ✅ 반드시 추가
app.add_middleware(
    SessionMiddleware,
    secret_key = os.getenv("SECRET_KEY", "default-secret"),
    session_cookie="session",       # 쿠키 이름 (기본은 "session")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 라우터 등록
app.include_router(user_router.router)
app.include_router(post_router.router)
app.mount("/static", StaticFiles(directory="img_store"), name="static")
