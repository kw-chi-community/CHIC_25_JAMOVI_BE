from fastapi import Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)



load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")

async def auth_middleware(request: Request, call_next):
    # 인증 필요x 엔드포인트
    public_paths = ["/auth/login", "/auth/register", "/auth/send-verification", "/docs", "/openapi.json"]
    
    # prefix가 /test or public_paths에 포함되면 인증x
    if request.url.path.startswith("/test") or request.url.path in public_paths:
        response = await call_next(request)
        return response

    try:
        token = request.headers.get('Authorization')
        if not token:
            raise HTTPException(status_code=401, detail="not exist token")

        token = token.split(" ")[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # request.state에 유저 정보(id) 저장
        request.state.user = payload
        
        response = await call_next(request)
        return response
        
    except (JWTError, IndexError):
        return JSONResponse(
            status_code=401,
            content={"message": "invalid token"}
        )

async def get_current_user(request: Request = None, websocket: WebSocket = None):
    try:
        logger.info(f"get_current_user")
        if websocket:
            logger.info(f"websocket: {websocket}")
            token = websocket.query_params.get('token')
        else:
            logger.info(f"request: {request}")
            token = request.headers.get('Authorization')

        if not token:
            if websocket:
                await websocket.close(code=4001, reason="Token not found")
                return None
            raise HTTPException(status_code=401, detail="not exist token")

        if not websocket:
            token = token.split(" ")[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
        
    except (JWTError, IndexError):
        if websocket:
            await websocket.close(code=4002, reason="Invalid token")
            return None
        raise HTTPException(
            status_code=401,
            detail="invalid token"
        )
