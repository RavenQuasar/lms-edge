from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api import auth, users, assignments, attendance, board, stats, system
from app.websocket import manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LMS-Edge application...")
    init_db()
    yield
    logger.info("Shutting down LMS-Edge application...")


app = FastAPI(
    title="LMS-Edge",
    description="班级局域网教学管理系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["作业"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["考勤"])
app.include_router(board.router, prefix="/api/board", tags=["白板"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])
app.include_router(manager.router)


@app.get("/")
async def root():
    return {"message": "LMS-Edge API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
