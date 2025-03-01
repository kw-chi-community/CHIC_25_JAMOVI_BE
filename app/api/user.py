from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from models import get_db, User
import logging
from middleware.auth import get_current_user

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

@router.get("/")
def get_user(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    logger.info(f"current_user: {current_user}")
    user = db.query(User).filter(User.id == current_user["user"]).first()
    if not user:
        logger.error(f"User not found: {current_user}")
        raise HTTPException(status_code=404, detail="User not found")
        
    email_prefix = user.email.split('@')[0]
    logger.info(f"user_id: {user.id}, email: {email_prefix}")
    return {
        "user_id": user.id,
        "email": email_prefix
    }
