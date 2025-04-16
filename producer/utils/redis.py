
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

def is_token_blacklisted(payload):
    try:
        jti = payload.get("jti")
        # Check if the jti exists in Redis
        return redis_client.exists(f"blacklist:{jti}") == 1
    except Exception as e:
        print(f"Error verifying token blacklist: {e}")
        return True