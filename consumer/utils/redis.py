import redis

import os
from datetime import datetime

from jose import jwt

from consumer.core.exceptions import InternalServerError

redis_client = redis.Redis(host='redis', port=6379, db=0)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def blacklist_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = decoded.get("jti")
        exp_timestamp = decoded.get("exp")
        
        if jti is None or exp_timestamp is None:
            raise ValueError("Token does not contain required jti or exp claim")
        
        current_timestamp = datetime.utcnow().timestamp()
        ttl = int(exp_timestamp - current_timestamp)
        if ttl > 0:
            redis_client.setex(f"blacklist:{jti}", ttl, "true")
    except Exception as e:
        raise InternalServerError(f"Error blacklisting token: {str(e)}")
