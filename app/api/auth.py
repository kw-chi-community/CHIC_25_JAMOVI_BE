from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os

from models import get_db, User
from utils import verify_password, create_access_token, get_password_hash
from crud import authenticate_user, create_user
from pydantic import EmailStr, BaseModel

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

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

verification_codes = {}

mail_config = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_SSL_TLS = False,
    MAIL_STARTTLS = True,
    USE_CREDENTIALS = True
)

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
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
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "token": None, "detail": str(e)}
        )

class EmailSchema(BaseModel):
    email: EmailStr

@router.post("/send-verification")
async def send_verification_code(email_data: EmailSchema):
    email = email_data.email
    logger.info(email)

    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
        
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

    logger.info("인증 코드", code)
    
    fm = FastMail(mail_config)
    await fm.send_message(message)
    return {"success": True, "detail": "Verification code sent"}

class RegisterForm(BaseModel):
    email: EmailStr
    password: str
    verification_code: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    form_data: RegisterForm,
    db: Session = Depends(get_db)
):
    try:
        logger.info("이메일", form_data.email)
        logger.info("비밀번호", form_data.password)
        logger.info("인증코드", form_data.verification_code)

        stored_data = verification_codes.get(form_data.email)
        if not stored_data:
            raise HTTPException(
                status_code=400,
                detail="Please request verification code first"
            )
    
        logger.info(stored_data)
            
        if stored_data["code"] != form_data.verification_code:
            raise HTTPException(
                status_code=400,
                detail="Invalid verification code"
            )
            
        if datetime.now() - stored_data["timestamp"] > timedelta(minutes=10):
            verification_codes.pop(form_data.email, None)
            raise HTTPException(
                status_code=400,
                detail="Verification code expired"
            )
        
        new_user = create_user(db, form_data.email, form_data.password)
        access_token = create_access_token(
            data={"user": new_user.id}
        )
        
        verification_codes.pop(form_data.email, None)
        
        return {"success": True, "token": access_token, "detail": "User created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "token": None, "detail": str(e)}
        )
