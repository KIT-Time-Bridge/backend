import uuid
from database.redis_conn import r

class SessionManager:
    def __init__(self, redis_client=r, ttl: int = 3600):
        """
        :param redis_client: Redis 연결 객체
        :param ttl: 세션 만료 시간 (초 단위, 기본 1시간)
        """
        self.r = redis_client
        self.ttl = ttl

    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.r.setex(f"session:{session_id}", self.ttl, user_id)
        return session_id

    def get_user(self, session_id: str) -> str | None:
        result = self.r.get(f"session:{session_id}")
        if result:
            # Redis에서 반환된 값이 bytes일 수 있으므로 decode
            if isinstance(result, bytes):
                return result.decode('utf-8')
            return result
        return None

    def delete_session(self, session_id: str) -> int:
        return self.r.delete(f"session:{session_id}")

    def refresh_session(self, session_id: str) -> bool:
        user_id = self.get_user(session_id)
        if user_id:
            self.r.setex(f"session:{session_id}", self.ttl, user_id)
            return True
        return False

    def is_valid(self, session_id: str) -> bool:
        return self.r.exists(f"session:{session_id}") == 1