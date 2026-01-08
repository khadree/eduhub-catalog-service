"""Main FastAPI application"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.cache import cache
from app.api import courses, enrollments, teachers, students, categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await init_db()
    await cache.connect()
    yield
    # Shutdown
    await cache.disconnect()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(courses.router, prefix="/api/v1")
app.include_router(enrollments.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")



@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready"}
