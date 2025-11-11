from datetime import date
from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from repository.post_repository import PostRepository
from io import BytesIO
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any,List
import os
import shutil
import httpx

# 벡터DB/유사도 서버 (insert/update/delete)
AI_SERVERS_Insert = [
    "http://localhost:8002/insert",
]
AI_SERVERS_Update = [
    "http://localhost:8002/update",
]
AI_SERVERS_Delete = [
    "http://localhost:8002/delete",
]
# 에이징 전용 서버
AGING_SERVER = "http://localhost:8000/generate"
img_url = "http://localhost:8002/similarity"


class PostService:

    # ✅ Aging 요청
    async def img_aging(self, missing_birth: date, img: UploadFile):
        today = date.today()
        target_age = today.year - missing_birth.year
        if (today.month, today.day) < (missing_birth.month, missing_birth.day):
            target_age -= 1

        file_bytes = await img.read()

        async with httpx.AsyncClient() as client:
            files = {"file": (img.filename, file_bytes, img.content_type)}
            resp = await client.post(f"{AGING_SERVER}?target_age={target_age}", files=files)

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AI 서버 요청 실패: {resp.text}")

        media_type = resp.headers.get("content-type", "").lower()
        if media_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식: {media_type}")

        return StreamingResponse(BytesIO(resp.content), media_type=media_type)

    #  등록된 실종글 검색
    def register_missing_search(self, user_id: str, db: Session):
        repo = PostRepository(db)
        return repo.get_register_missing_by_id(user_id)

    def all_missing_search_by_family(self, pageNum: int, db: Session):
        repo = PostRepository(db)
        return repo.get_all_missing_fp(pageNum, 12)

    def all_missing_search_by_missing(self, pageNum: int, db: Session):
        repo = PostRepository(db)
        return repo.get_all_missing_mp(pageNum, 12)

    def detail_missing_search(self, db: Session, missing_id: str):
        repo = PostRepository(db)
        if missing_id[0] == "m":
            return repo.get_missing_post_by_id(missing_id)
        else:
            return repo.get_family_post_by_id(missing_id)

    # ✅ 게시글 삭제
    async def delete_post(self, db: Session, post_id: str) -> bool:
        repo = PostRepository(db)

        if post_id.startswith("m"):
            post = repo.get_missing_post_by_id(post_id)
        elif post_id.startswith("f"):
            post = repo.get_family_post_by_id(post_id)
        else:
            raise HTTPException(status_code=400, detail="post_id 형식이 잘못되었습니다.")

        if not post:
            raise HTTPException(status_code=404, detail="해당 게시글을 찾을 수 없습니다.")

        # 이미지 삭제
        image_urls = [
            getattr(post, "face_img_origin", None),
            getattr(post, "face_img_aging", None),
        ]
        for url in image_urls:
            if url:
                # 절대 URL → 실제 파일 경로 변환
                file_path = url.replace("/static/", "img_store/")
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"[INFO] 이미지 삭제 완료: {file_path}")
                    except Exception as e:
                        print(f"[ERROR] 이미지 삭제 실패: {file_path}, {e}")
                else:
                    print(f"[WARN] 파일 없음: {file_path}")

        repo.delete_missing_post(post)

        # AI 서버에 삭제 요청
        payload = {"post_id": post_id}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for server in AI_SERVERS_Delete:
                    resp = await client.post(server, json=payload)
                    if resp.status_code == 200:
                        print(f"[INFO] 벡터DB 삭제 요청 성공: {server}")
                    else:
                        print(f"[WARN] 벡터DB 삭제 요청 실패: {server}, code={resp.status_code}")
        except Exception as e:
            print(f"[ERROR] 벡터DB 삭제 요청 중 예외 발생: {e}")

        return True

    # ✅ 게시글 수정
    async def post_update(
        self,
        db: Session,
        missing_id: str,
        type: Optional[int] = None,
        missing_name: Optional[str] = None,
        gender: Optional[str] = None,
        missing_birth: Optional[date] = None,
        img_origin: Optional[UploadFile] = None,
        img_aging: Optional[UploadFile] = None,
        missing_date: Optional[date] = None,
        missing_situation: Optional[str] = None,
        missing_extra_evidence: Optional[str] = None,
        missing_place: Optional[str] = None,
        photo_age: Optional[int] = None,
    ):
        repo = PostRepository(db)
        post = repo.update_post(
            missing_id=missing_id,
            type=type,
            missing_name=missing_name,
            gender=gender,
            missing_birth=missing_birth,
            missing_date=missing_date,
            missing_situation=missing_situation,
            missing_extra_evidence=missing_extra_evidence,
            missing_place=missing_place,
            photo_age=photo_age,
        )
        if not post:
            raise HTTPException(status_code=404, detail="수정할 게시글을 찾을 수 없습니다.")

        type_dir = "family" if missing_id.startswith("f") else "missing"
        base_dir = os.path.join("img_store", type_dir, missing_id)
        os.makedirs(base_dir, exist_ok=True)

        ai_send_needed = False
        ai_file = None
        ai_filename = None

        # origin.png 갱신
        if img_origin:
            origin_path = os.path.join(base_dir, "origin.png")
            if os.path.exists(origin_path):
                os.remove(origin_path)
            img_origin.file.seek(0)
            with open(origin_path, "wb") as buffer:
                shutil.copyfileobj(img_origin.file, buffer)

            origin_url = "{type_dir}/{missing_id}/origin.png"
            post.face_img_origin = origin_url
            print(f"[INFO] origin 이미지 교체 완료: {origin_path}")

            if missing_id.startswith("m"):
                ai_send_needed = True
                with open(origin_path, "rb") as f:
                    ai_file = ("origin.png", f.read(), img_origin.content_type)
                ai_filename = "origin.png"

        # aging.png 갱신
        if img_aging and hasattr(post, "face_img_aging"):
            aging_path = os.path.join(base_dir, "aging.png")
            if os.path.exists(aging_path):
                os.remove(aging_path)
            img_aging.file.seek(0)
            with open(aging_path, "wb") as buffer:
                shutil.copyfileobj(img_aging.file, buffer)

            aging_url = f"{type_dir}/{missing_id}/aging.png"
            post.face_img_aging = aging_url
            print(f"[INFO] aging 이미지 교체 완료: {aging_path}")

            if missing_id.startswith("f"):
                ai_send_needed = True
                with open(aging_path, "rb") as f:
                    ai_file = ("aging.png", f.read(), img_aging.content_type)
                ai_filename = "aging.png"

        try:
            db.commit()
            print(f"[INFO] 게시글 및 이미지 업데이트 완료: {missing_id}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"게시글 업데이트 실패: {e}")

        # AI 서버 업데이트
        if ai_send_needed and ai_file:
            try:
                async with httpx.AsyncClient() as client:
                    for server in AI_SERVERS_Update:
                        files = {"img": ai_file}
                        data = {
                            "gender_id": str(post.gender_id),
                            "type": str(type) if type else ("1" if missing_id.startswith("f") else "2"),
                            "missing_id": missing_id,
                        }
                        resp = await client.post(server, data=data, files=files)
                        if resp.status_code == 200:
                            print(f"[INFO] AI 서버 업데이트 요청 성공: {server}")
                        else:
                            print(f"[WARN] AI 서버 업데이트 요청 실패: {server}, code={resp.status_code}")
            except Exception as e:
                print(f"[ERROR] AI 서버 업데이트 요청 중 예외 발생: {e}")
        else:
            print(f"[INFO] AI 서버 업데이트 조건 불충족 → ai_send_needed={ai_send_needed}, ai_file={ai_file}")

        return True
     # ✅ 이미지 유사도 검색
    async def image_similarity(
        self,
        missing_id: str,
        db,
        exclude_user_id: Optional[str] = None,
        limit: Optional[int] = None,  # 예: 상위 N개만 보고 싶으면 사용
    ) -> Dict[str, Any]:
        repo = PostRepository(db)

        # 1) 타깃 로드 + 직렬화 함수/타입 결정
        if not missing_id:
            raise HTTPException(status_code=400, detail="missing_id가 필요해요.")

        if missing_id[0] == "m":
            target_post = repo.get_missing_post_by_id(missing_id)
            serialize_fn = self.serialize_missing_post
            type_value = 2
        else:
            target_post = repo.get_family_post_by_id(missing_id)
            serialize_fn = self.serialize_family_post
            type_value = 1

        if not target_post:
            raise HTTPException(status_code=404, detail="타깃 게시글을 찾을 수 없어요.")

        # 2) 외부 이미지 유사도 API 호출
        payload = {
            "type": type_value,
            "gender": getattr(target_post, "gender_id", None),
            "missingId": missing_id
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(img_url, params=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            # 외부 서비스 오류는 502 정도로 넘기는 게 보통 좋아요
            raise HTTPException(status_code=502, detail=f"이미지 유사도 서비스 오류: {str(e)}")

        # 3) 결과 정렬 (score desc)
        raw_results: List[Dict[str, Any]] = sorted(
            data.get("result", []),
            key=lambda r: r.get("score", 0.0),
            reverse=True
        )

        # 4) 타깃 자신/내 글 제외 필터링
        filtered_results: List[Dict[str, Any]] = []
        for r in raw_results:
            sim_id = r.get("missingId")
            score = r.get("score", 0.0)
            if not sim_id:
                continue
            if sim_id == missing_id:
                continue  # 타깃 자신 제외

            # 이 시점엔 user_id를 모르므로, DB 로드 후 필터링
            filtered_results.append({"missingId": sim_id, "score": score})

        # (선택) 상위 N개로 자르기 — DB 부하를 줄이고 싶을 때 유용
        if limit is not None and limit > 0:
            filtered_results = filtered_results[:limit]

        # 5) 결과를 실제 게시글로 변환 + 내 글 제외
        similar_posts = []
        for item in filtered_results:
            sim_id, score = item["missingId"], item["score"]

            if sim_id[0] == "m":
                sim_post = repo.get_missing_post_by_id(sim_id)
                if not sim_post:
                    continue
                # 내 글 제외
                if exclude_user_id and getattr(sim_post, "user_id", None) == exclude_user_id:
                    continue
                sim_serialized = self.serialize_missing_post(sim_post)
            else:
                sim_post = repo.get_family_post_by_id(sim_id)
                if not sim_post:
                    continue
                # 내 글 제외
                if exclude_user_id and getattr(sim_post, "user_id", None) == exclude_user_id:
                    continue
                sim_serialized = self.serialize_family_post(sim_post)

            similar_posts.append({"post": sim_serialized, "score": score})

        return {
            "targetPost": serialize_fn(target_post),
            "similarPosts": similar_posts
        }

    def serialize_missing_post(self, post) -> dict:
        return {
            "mp_id": post.mp_id,
            "face_img_origin": post.face_img_origin,
            "missing_date": post.missing_date,
            "missing_name": post.missing_name,
            "missing_situation": post.missing_situation,
            "missing_birth": post.missing_birth,
            "missing_place": post.missing_place,
            "missing_extra_evidence": post.missing_extra_evidence,
            "user_id": post.user_id,
            "gender_id": post.gender_id,
        }

    def serialize_family_post(self, post) -> dict:
        return {
            "fp_id": post.fp_id,
            "face_img_aging": post.face_img_aging,
            "face_img_origin": post.face_img_origin,
            "photo_age": post.photo_age,
            "missing_birth": post.missing_birth,
            "missing_date": post.missing_date,
            "missing_name": post.missing_name,
            "missing_situation": post.missing_situation,
            "missing_extra_evidence": post.missing_extra_evidence,
            "missing_place": post.missing_place,
            "user_id": post.user_id,
            "gender_id": post.gender_id,
        }

    # ✅ 게시글 등록
    async def post_upload(
        self,
        user_id: str,
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
        print(f"[DEBUG] post_upload 시작 - user_id={user_id}, type={type}, missing_name={missing_name}")

        if gender == "남":
            gender_id = 1
        elif gender == "여":
            gender_id = 2
        else:
            raise HTTPException(status_code=400, detail="gender는 '남' 또는 '여'만 가능합니다.")

        repo = PostRepository(db)

        if type == 1:  # FamilyPost
            num = repo.get_max_fp() + 1
            post_id = "f" + str(num).zfill(7)
        elif type == 2:  # MissingPost
            num = repo.get_max_mp() + 1
            post_id = "m" + str(num).zfill(7)
        else:
            raise HTTPException(status_code=400, detail="잘못된 type 값입니다. (1=FamilyPost, 2=MissingPost)")

        print(f"[DEBUG] 생성된 post_id={post_id}")

        type_dir = "family" if type == 1 else "missing"
        base_dir = os.path.join("img_store", type_dir, post_id)
        os.makedirs(base_dir, exist_ok=True)

        origin_path = os.path.join(base_dir, "origin.png") if img_origin else None
        aging_path = os.path.join(base_dir, "aging.png") if img_aging else None

        origin_url = f"{type_dir}/{post_id}/origin.png" if img_origin else None
        aging_url = f"{type_dir}/{post_id}/aging.png" if img_aging else None

        if type == 1:
            repo.add_fp(
                fp_id=post_id,
                face_img_origin=origin_url,
                face_img_aging=aging_url,
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
            if img_origin and origin_path:
                img_origin.file.seek(0)
                with open(origin_path, "wb") as buffer:
                    shutil.copyfileobj(img_origin.file, buffer)
            if img_aging and aging_path:
                img_aging.file.seek(0)
                with open(aging_path, "wb") as buffer:
                    shutil.copyfileobj(img_aging.file, buffer)

        elif type == 2:
            repo.add_mp(
                mp_id=post_id,
                face_img_origin=origin_url,
                missing_date=missing_date,
                missing_name=missing_name,
                missing_situation=missing_situation,
                missing_birth=missing_birth,
                missing_place=missing_place,
                missing_extra_evidence=missing_extra_evidence,
                user_id=user_id,
                gender_id=gender_id,
            )
            if img_origin and origin_path:
                img_origin.file.seek(0)
                with open(origin_path, "wb") as buffer:
                    shutil.copyfileobj(img_origin.file, buffer)

        ai_send_file = None
        ai_filename = None
        if type == 2 and img_origin and origin_path:
            with open(origin_path, "rb") as f:
                ai_send_file = ("origin.png", f.read(), img_origin.content_type)
            ai_filename = "origin.png"
        elif type == 1 and img_aging and aging_path:
            with open(aging_path, "rb") as f:
                ai_send_file = ("aging.png", f.read(), img_aging.content_type)
            ai_filename = "aging.png"

        if ai_send_file:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    for server in AI_SERVERS_Insert:
                        files = {"img": ai_send_file}
                        data = {
                            "gender_id": str(gender_id),
                            "type": str(type),
                            "missing_id": post_id,
                        }
                        resp = await client.post(server, data=data, files=files)
                        if resp.status_code == 200:
                            print(f"[INFO] AI 서버 업로드 성공: {server}, file={ai_filename}")
                        else:
                            print(f"[WARN] AI 서버 업로드 실패: {server}, code={resp.status_code}")
            except Exception as e:
                print(f"[ERROR] AI 서버 업로드 중 예외 발생: {e}")

        return True
