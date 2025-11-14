from sqlalchemy.orm import Session
from repository.post_model import FamilyPost, MissingPost
from sqlalchemy import func, cast, Integer, or_, and_
from typing import Optional
from datetime import date, datetime
import math

class PostRepository:
    def __init__(self, db: Session):
        # DB 세션 주입 (트랜잭션 단위로 동작)
        self.db = db

    def get_max_fp(self) -> int:
        """family_post 테이블의 가장 큰 번호 반환 (없으면 0)"""
        max_val = (
            self.db.query(
                func.max(
                    cast(func.substring(FamilyPost.fp_id, 2), Integer)  # 'f0000003' → '0000003' → 3
                )
            ).scalar()
        )
        return max_val if max_val is not None else 0

    def get_max_mp(self) -> int:
        """missing_post 테이블의 가장 큰 번호 반환 (없으면 0)"""
        max_val = (
            self.db.query(
                func.max(
                    cast(func.substring(MissingPost.mp_id, 2), Integer)  # 'm0000003' → '0000003' → 3
                )
            ).scalar()
        )
        return max_val if max_val is not None else 0
    
    def add_fp(
        self,
        fp_id: str,
        face_img_origin: str,
        face_img_aging: str,
        photo_age: int,
        missing_birth: date,
        missing_date: Optional[date],
        missing_name: str,
        missing_situation: Optional[str],
        missing_extra_evidence: Optional[str],
        missing_place: Optional[str],
        user_id: str,
        gender_id: int
    ):
        new_post = FamilyPost(
            fp_id=fp_id,
            face_img_origin=face_img_origin,
            face_img_aging=face_img_aging,
            photo_age=photo_age,
            missing_birth=missing_birth,
            missing_date=missing_date,
            missing_name=missing_name,
            missing_situation=missing_situation,
            missing_extra_evidence=missing_extra_evidence,
            missing_place=missing_place,
            user_id=user_id,
            gender_id=gender_id,
        )
        self.db.add(new_post)
        self.db.commit()
        return True

    def add_mp(
        self,
        mp_id: str,
        face_img_origin: str,
        missing_date: Optional[date],
        missing_name: str,
        missing_situation: Optional[str],
        missing_birth: Optional[date],
        missing_place: Optional[str],
        missing_extra_evidence: Optional[str],
        user_id: str,
        gender_id: int
    ):
        new_post = MissingPost(
            mp_id=mp_id,
            face_img_origin=face_img_origin,
            missing_date=missing_date,
            missing_name=missing_name,
            missing_situation=missing_situation,
            missing_birth=missing_birth,
            missing_place=missing_place,
            missing_extra_evidence=missing_extra_evidence,
            user_id=user_id,
            gender_id=gender_id,
        )
        self.db.add(new_post)
        self.db.commit()
        return True
    def get_register_missing_by_id(self,user_id):
          # FamilyPost에서 user_id로 조회
        family_posts = (
            self.db.query(FamilyPost)
            .filter(FamilyPost.user_id == user_id)
            .all()
        )

        # MissingPost에서 user_id로 조회
        missing_posts = (
            self.db.query(MissingPost)
            .filter(MissingPost.user_id == user_id)
            .all()
        )

        # 두 결과 합치기
        return {
            "family_posts": family_posts,
            "missing_posts": missing_posts
        }
    
    def get_all_missing_fp(self, pageNum: int,  pageSize: int = 12, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None):
        offset = (pageNum - 1) * pageSize

        # ✅ 게시글 데이터 조회 (승인된 게시글만)
        query = self.db.query(FamilyPost).filter(
            (FamilyPost.isAccept == True) | (FamilyPost.isAccept.is_(None))
        )

        # 통합 검색: search_keywords를 이름, 실종상황, 추가단서에서 모두 검색
        if search_keywords:
            keywords = search_keywords.split()  # 띄어쓰기로 키워드 분리
            conditions = []
            for keyword in keywords:
                keyword_condition = or_(
                    FamilyPost.missing_name.like(f"%{keyword}%"),
                    FamilyPost.missing_situation.like(f"%{keyword}%"),
                    FamilyPost.missing_extra_evidence.like(f"%{keyword}%")
                )
                conditions.append(keyword_condition)
            if conditions:
                # 모든 키워드가 포함되어야 함 (AND 조건)
                query = query.filter(and_(*conditions))
        
        if gender_id:
            query = query.filter(FamilyPost.gender_id == gender_id)
        if missing_birth:
            birth_date = datetime.strptime(missing_birth, "%Y-%m-%d").date()
            query = query.filter(FamilyPost.missing_birth == birth_date)
        if missing_date:
            date_obj = datetime.strptime(missing_date, "%Y-%m-%d").date()
            query = query.filter(FamilyPost.missing_date == date_obj)
        if missing_place:
            query = query.filter(FamilyPost.missing_place.like(f"%{missing_place}%"))

        # 전체 개수 조회 (필터링 후)
        total_count = query.count()

        posts = (
            query.order_by(FamilyPost.fp_id)
            .offset(offset)
            .limit(pageSize)
            .all()
        )

        # ✅ 최대 페이지 수 계산
        total_pages = math.ceil(total_count / pageSize) if total_count > 0 else 1

        return {
            "posts": posts,
            "total_count": total_count,   # 전체 게시글 수
            "page_size": pageSize,        # 페이지당 크기
            "current_page": pageNum,      # 현재 페이지
            "total_pages": total_pages    # 전체 페이지 수
        }


    def get_all_missing_mp(self, pageNum: int,  pageSize: int = 12, search_keywords: Optional[str] = None, gender_id: Optional[int] = None, missing_birth: Optional[str] = None, missing_date: Optional[str] = None, missing_place: Optional[str] = None):
        offset = (pageNum - 1) * pageSize

        # ✅ 게시글 데이터 조회 (승인된 게시글만)
        query = self.db.query(MissingPost).filter(MissingPost.isAccept == True)

        # 통합 검색: search_keywords를 이름, 실종상황, 추가단서에서 모두 검색
        if search_keywords:
            keywords = search_keywords.split()  # 띄어쓰기로 키워드 분리
            conditions = []
            for keyword in keywords:
                keyword_condition = or_(
                    MissingPost.missing_name.like(f"%{keyword}%"),
                    MissingPost.missing_situation.like(f"%{keyword}%"),
                    MissingPost.missing_extra_evidence.like(f"%{keyword}%")
                )
                conditions.append(keyword_condition)
            if conditions:
                # 모든 키워드가 포함되어야 함 (AND 조건)
                query = query.filter(and_(*conditions))
        
        if gender_id:
            query = query.filter(MissingPost.gender_id == gender_id)
        if missing_birth:
            birth_date = datetime.strptime(missing_birth, "%Y-%m-%d").date()
            query = query.filter(MissingPost.missing_birth == birth_date)
        if missing_date:
            date_obj = datetime.strptime(missing_date, "%Y-%m-%d").date()
            query = query.filter(MissingPost.missing_date == date_obj)
        if missing_place:
            query = query.filter(MissingPost.missing_place.like(f"%{missing_place}%"))

        # 전체 개수 조회 (필터링 후)
        total_count = query.count()

        posts = (
            query.order_by(MissingPost.mp_id)
            .offset(offset)
            .limit(pageSize)
            .all()
        )

        # ✅ 최대 페이지 수 계산
        total_pages = math.ceil(total_count / pageSize) if total_count > 0 else 1

        return {
            "posts": posts,
            "total_count": total_count,
            "page_size": pageSize,
            "current_page": pageNum,
            "total_pages": total_pages
        }

    def get_user_id_by_missing_id(self, type,missing_id):
        if type == 1:
            # FamilyPost 조회
            post = self.db.get(FamilyPost, missing_id)
        else:
            # MissingPost 조회
            post = self.db.get(MissingPost, missing_id)

        if not post:
            return None
        
        return post.user_id
    
    def get_missing_post_by_id(self, missing_id):
        return self.db.query(MissingPost).filter(MissingPost.mp_id==missing_id).first()
    
    def get_family_post_by_id(self, missing_id):
        return self.db.query(FamilyPost).filter(FamilyPost.fp_id==missing_id).first()
    
    def delete_missing_post(self, missing_post):
        try:
            self.db.delete(missing_post)
            self.db.commit()
            print(f"[INFO] DB에서 post_id={missing_post} 삭제 완료")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] DB 삭제 실패: {e}")
            return False
        
    def update_post(
    self,
    missing_id: str,
    type: Optional[int] = None,
    missing_name: Optional[str] = None,
    gender: Optional[str] = None,
    missing_birth: Optional[date] = None,
    missing_date: Optional[date] = None,
    missing_situation: Optional[str] = None,
    missing_extra_evidence: Optional[str] = None,
    missing_place: Optional[str] = None,
    photo_age: Optional[int] = None,
):
        # 1️⃣ 게시글 가져오기
        if missing_id.startswith("m"):
            post = self.get_missing_post_by_id(missing_id)
        elif missing_id.startswith("f"):
            post = self.get_family_post_by_id(missing_id)
        else:
            raise ValueError("post_id 형식이 잘못되었습니다.")

        if not post:
            raise ValueError(f"{missing_id} 게시글을 찾을 수 없습니다.")

        # 2️⃣ 값이 None이 아닐 때만 업데이트
        if missing_name is not None:
            post.missing_name = missing_name

        if gender is not None:
            post.gender_id = 1 if gender == "남" else 2

        if missing_birth is not None:
            post.missing_birth = missing_birth

        if missing_date is not None:
            post.missing_date = missing_date

        if missing_situation is not None:
            post.missing_situation = missing_situation

        if missing_extra_evidence is not None:
            post.missing_extra_evidence = missing_extra_evidence

        if missing_place is not None:
            post.missing_place = missing_place

        if type == 1 and photo_age is not None and hasattr(post, "photo_age"):
            post.photo_age = photo_age

        # 3️⃣ DB 반영
        try:
            self.db.commit()
            print(f"[INFO] DB 업데이트 완료: post_id={missing_id}")
            return post   # ✅ ORM 객체 반환
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] DB 업데이트 실패: {e}")
            return None   # 실패 시 None 반환
