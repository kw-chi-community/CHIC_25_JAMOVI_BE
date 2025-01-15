from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from models import get_db, User
from utils import verify_password, create_access_token, get_password_hash
from schemas import UserCreate
from crud import authenticate_user, create_user
from logging import getLogger

logger = getLogger(__name__)
router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"user": user.email},
    )
    return access_token


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Registering user: {user_data.email}")
    new_user = create_user(db, user_data.email, user_data.password)
    access_token = create_access_token(
        data={"user": new_user.email}
    )
    return access_token