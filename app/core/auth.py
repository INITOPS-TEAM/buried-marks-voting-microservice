import os

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "public.pem")


def get_public_key():
    with open(PUBLIC_KEY_PATH, "r") as f:
        return f.read()


async def verify_jwt(auth: HTTPAuthorizationCredentials = Security(security)):
    token = auth.credentials
    try:
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=["ES256"])

        # We get the fields
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")
        inspector = payload.get("inspector", False)

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        return {
            "user_id": user_id,
            "username": username,
            "role": role,
            "inspector": inspector,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
