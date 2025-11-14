# services/user_service.py
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.header import Header
import os
from dotenv import load_dotenv
from fastapi import HTTPException

from repository.post_repository import PostRepository
from repository.user_repository import UserRepository   # DAO → Repository로 명확화
from repository.user_model import User                  # ORM 엔티티
from schemas.user_schema import UserCreate, UserLogin   # Pydantic DTO (입력만 사용)
from services.session_service import SessionManager

# .env 파일 로드
load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def register_user(self, db: Session, data: UserCreate) -> bool:
        repo = UserRepository(db)
        # 1) 이메일 중복 체크
        if repo.get_by_email(data.email):

            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        if repo.get_by_id(data.username):
            raise HTTPException(status_code=400, detail="이미 등록된 아이디입니다.")


        # 2) 비밀번호 해시
        hashed_pw = pwd_context.hash(data.password)

        # 3) 엔티티 생성 (DTO → Entity 변환)
        user = User(
            user_id=data.username,
            user_name=data.name,
            user_email=data.email,
            user_pw=hashed_pw,
            birthday=data.birth,
        )

        # 4) 저장 + 트랜잭션 커밋(서비스에서)
        repo.add(user)

        # 5) 성공 여부만 반환
        return True

    def login(self, db: Session, user_id: str, password: str, session_manager: SessionManager):
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")
        if not pwd_context.verify(password, user.user_pw):
            raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")

        # ✅ 세션 생성
        session_id = session_manager.create_session(user_id)
        return  session_id

    def delete_user(self, db: Session, user_id: str):
        repo = UserRepository(db)
        deleted = repo.delete_by_id(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")
        return True


    async def send_email(self, user_id: str, text: str, db: Session, missing_id: str) -> bool:
        if not user_id:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        if not missing_id:
            raise HTTPException(status_code=400, detail="게시글 ID가 필요합니다.")
        if not text:
            raise HTTPException(status_code=400, detail="메일 내용이 필요합니다.")
            
        user_repo = UserRepository(db)
        post_repo = PostRepository(db)
        subject = "타임브릿지에 연락이 도착하였습니다."

        # SMTP 설정
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "nhw4567@gmail.com"
        sender_password = os.getenv("GMAIL_APP_PASSWORD")  # 환경 변수에서 불러오기
        
        if not sender_password:
            print("경고: GMAIL_APP_PASSWORD 환경 변수가 설정되지 않았습니다.")
            print("현재 환경 변수:", os.environ.get("GMAIL_APP_PASSWORD", "없음"))
            raise HTTPException(
                status_code=500, 
                detail="메일 서버 설정 오류입니다. GMAIL_APP_PASSWORD 환경 변수를 설정해주세요."
            )

        # missing_id로 게시글 작성자 찾기
        if not missing_id or len(missing_id) == 0:
            raise HTTPException(status_code=400, detail="잘못된 게시글 ID입니다.")
            
        if missing_id[0] == "m":
            type = 2
        else:
            type = 1

        user_id_of_post = post_repo.get_user_id_by_missing_id(type, missing_id)
        if not user_id_of_post:
            raise HTTPException(status_code=404, detail="게시글 작성자를 찾을 수 없습니다.")

        # 게시글 작성자 이메일 가져오기
        post_user = user_repo.get_by_id(user_id_of_post)
        if not post_user:
            raise HTTPException(status_code=404, detail="게시글 작성자 정보를 찾을 수 없습니다.")
        to_email = post_user.user_email

        # 메일 보낸 사람 정보 추가
        sender_user = user_repo.get_by_id(user_id)
        if sender_user:
            extra_info = f"\n\n[보낸 사람 정보]\n이름: {sender_user.user_name}\n이메일: {sender_user.user_email}"
        else:
            extra_info = "\n\n[보낸 사람 정보 없음]"

        full_text = text + extra_info

        # 메일 메시지 작성
        msg = MIMEMultipart()
        msg["From"] = formataddr(("타임브릿지", sender_email))
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8")
        msg.attach(MIMEText(full_text, "plain"))

        # 메일 전송 (비동기로 처리)
        import asyncio
        try:
            # SMTP 작업을 별도 스레드에서 실행하여 블로킹 방지
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._send_smtp_email(smtp_server, smtp_port, sender_email, sender_password, to_email, msg)
            )
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"[ERROR] SMTP 인증 실패: {e}")
            raise HTTPException(status_code=500, detail=f"메일 인증에 실패했습니다. Gmail 앱 비밀번호를 확인해주세요.")
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP 오류: {e}")
            raise HTTPException(status_code=500, detail=f"SMTP 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            print(f"[ERROR] 메일 전송 실패: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"메일 전송에 실패했습니다: {str(e)}")
    
    def _send_smtp_email(self, smtp_server, smtp_port, sender_email, sender_password, to_email, msg):
        """SMTP 메일 전송 헬퍼 함수 (동기)"""
        with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
