from datetime import datetime, timedelta
import random
import string
from fastapi import HTTPException, status
from fastapi_mail import FastMail, MessageSchema
import logging
from sqlalchemy.orm import Session

from utils import create_access_token
from crud import authenticate_user, create_user
from models import get_db, User

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)
verification_codes = {}

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

async def send_verification_email(email: str, mail_config) -> dict:
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    db = next(get_db())
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
        
    code = generate_verification_code()
    verification_codes[email] = {
        "code": code,
        "timestamp": datetime.now()
    }
    
    message = MessageSchema(
        subject="Stat BEE 이메일 인증 코드",
        recipients=[email],
        body=f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="color: #333;">Stat BEE 이메일 인증</h1>
                    <p style="color: #666; font-size: 16px;">아래의 인증 코드를 입력해주세요.</p>
                    <div style="background-color: #ffffff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <span style="font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #007bff;">{code}</span>
                    </div>
                    <p style="color: #999; font-size: 14px;">이 인증 코드는 10분 동안 유효합니다.</p>
                </div>
            </body>
        </html>
        """,
        subtype="html"
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)
    return {"success": True, "detail": "Verification code sent"}

def verify_and_register(email: str, password: str, verification_code: str, db: Session) -> dict:
    stored_data = verification_codes.get(email)
    if not stored_data:
        raise HTTPException(
            status_code=400,
            detail="Please request verification code first"
        )
        
    if stored_data["code"] != verification_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )
        
    if datetime.now() - stored_data["timestamp"] > timedelta(minutes=10):
        verification_codes.pop(email, None)
        raise HTTPException(
            status_code=400,
            detail="Verification code expired"
        )
    
    new_user = create_user(db, email, password)
    access_token = create_access_token(
        data={"user": new_user.id}
    )
    
    verification_codes.pop(email, None)
    return {"success": True, "token": access_token, "detail": "User created successfully"}

def login_user(username: str, password: str, db: Session) -> dict:
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "token": None,
                "detail": "Incorrect email or password"
            }
        )
    access_token = create_access_token(
        data={"user": user.id},
    )
    return {"success": True, "token": access_token, "detail": "User logged in successfully"} 