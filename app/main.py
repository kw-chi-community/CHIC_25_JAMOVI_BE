from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import test_router
from contextlib import asynccontextmanager
from models import init_db
import logging


logger = logging.getLogger(__name__)

logging.basicConfig(filename='jamovi_be.log', level=logging.INFO)



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return "working..."

app.include_router(test_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
