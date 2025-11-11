from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from repository.user_model import User

class UserRepository:
    def __init__(self, db: Session):
        # DB 세션 주입 (트랜잭션 단위로 동작)
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        기본키(PK, user_id)로 사용자 조회
        - 있으면 User 객체 반환
        - 없으면 None 반환
        - SQL: SELECT * FROM app_user WHERE user_id = :user_id
        """
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회
        - SQLAlchemy select() 사용
        - 있으면 User 객체 반환, 없으면 None 반환
        - SQL: SELECT * FROM app_user WHERE user_email = :email
        """
        stmt = select(User).where(User.user_email == email)
        return self.db.execute(stmt).scalars().first()
    def add(self, user: User) -> User:
        """
        새로운 사용자 객체를 세션에 추가
        - 실제 DB INSERT는 commit()이 호출될 때 발생
        - 여기서는 세션에 등록만 함
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_by_id(self, user_id: str) -> bool:
            """
            user_id로 사용자 삭제
            - 존재하지 않으면 False
            - 삭제 성공하면 True
            """
            user = self.get_by_id(user_id)
            if not user:
                return False
            self.db.delete(user)
            self.db.commit()
            return True
