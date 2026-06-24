from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="CFRI API",
    description="Customer Feedback Revenue Intelligence",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import health
app.include_router(health.router, tags=["Health"])


@app.on_event("startup")
async def startup():
    print(f"🚀 CFRI API démarrée — env: {settings.app_env}")