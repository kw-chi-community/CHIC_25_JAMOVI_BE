from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import random
import string
from fastapi_mail import ConnectionConfig
import os
from models import get_db
from pydantic import EmailStr, BaseModel
from services import send_verification_email, verify_and_register, login_user
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

router = APIRouter()

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
        return login_user(form_data.username, form_data.password, db)
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
    return await send_verification_email(email, mail_config)

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
        
        return verify_and_register(form_data.email, form_data.password, form_data.verification_code, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "token": None, "detail": str(e)}
        )
