from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import test_router, auth, project, user, statistics
from middleware import auth_middleware
from contextlib import asynccontextmanager
from models import init_db
import os
from dotenv import load_dotenv
from utils import logger

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.middleware("http")(auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(project.router)
app.include_router(user.router)
app.include_router(statistics.router)

if __name__ == "__main__":
    logger.info("starting server")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
