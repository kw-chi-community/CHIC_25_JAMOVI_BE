from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from models import get_db, User
from utils import verify_password, create_access_token, get_password_hash
from crud import authenticate_user, create_user
from utils import logger

router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "token": None,
                    "detail": "Incorrect email or password"
                }
            )
        access_token = create_access_token(
            data={"user": user.id},
        )
        return {"success": True, "token": access_token, "detail": "User logged in successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "token": None, "detail": str(e)}
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        new_user = create_user(db, form_data.username, form_data.password)
        access_token = create_access_token(
            data={"user": new_user.id}
        )
        return {"success": True, "token": access_token, "detail": "User created successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "token": None, "detail": str(e)}
        )
