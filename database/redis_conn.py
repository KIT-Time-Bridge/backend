# database/redis_conn.py
import redis

# Redis 클라이언트 연결 (기본: localhost:6379)
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,                # DB index (0번 DB)
    decode_responses=True  # 문자열로 응답 받기
)
