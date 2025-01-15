from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import test_router, auth
from middleware import auth_middleware
from contextlib import asynccontextmanager
from models import init_db
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(filename='jamovi_be.log', level=logging.INFO)



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.middleware("http")(auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def token_test(request: Request):
    try:
        user = request.state.user
        return {
            "token": True,
            "user": user.get("user"),
            "env": os.getenv("ENV_TEST")
        }
    except AttributeError:
        return {
            "token": False,
            "user": None,
            "env": os.getenv("ENV_TEST")
        }

app.include_router(test_router.router)
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
