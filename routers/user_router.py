# routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from Controllers.user_controller import UserController
from schemas.user_schema import UserCreate, UserLogin
from schemas.user_schema import UserDelete  # 삭제용 (user_id만 필요)``
from fastapi.responses import JSONResponse
from fastapi import Response
from fastapi import Request, HTTPException

router = APIRouter(prefix="/api/users", tags=["users"])
# -----------------------------
# 회원가입
# -----------------------------
@router.post("/createuser", response_model=bool)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    controller = UserController()
    return controller.create_user(user, db)

# -----------------------------
# 회원 삭제
# -----------------------------
@router.delete("/delete", response_model=bool)
def delete_user(session_id: str, db: Session = Depends(get_db)):
    controller = UserController()
    result = controller.delete_user(session_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return True

# -----------------------------
# 로그인
# -----------------------------

@router.post("/login")
def login(user:UserLogin, request:Request, db: Session = Depends(get_db)):
    controller = UserController()
    return controller.login(user,db,request)
# -----------------------------
# 로그아웃
# -----------------------------
@router.post("/logout")
def logout(request:Request):
    controller = UserController()
    session_id=request.session.get("session_id")
    result = controller.logout(session_id)
    request.session.clear()             # ✅ 세션 쿠키 초기화
    if not result:
        raise HTTPException(status_code=400, detail="Logout failed")
    return JSONResponse(content={"message": "Logged out successfully"})

@router.post("/send_to_mail")
def send_mail(request:Request, missing_id:str, text:str, db: Session = Depends(get_db)):
    try:
        controller=UserController()
        session_id=request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        return controller.send_email(session_id, missing_id, text, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] send_to_mail 라우터 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")
@router.get("/status")
def session_status(request:Request):
    session_id=request.session.get("session_id")
    controller=UserController()
    return controller.session_is_vaild(session_id)
