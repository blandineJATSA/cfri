from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import SessionLocal

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

from app.api.routes import health, imports, analysis, dashboard
app.include_router(health.router, tags=["Health"])
app.include_router(imports.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)


@app.on_event("startup")
async def startup():
    print(f"🚀 CFRI API démarrée — env: {settings.app_env}")
    # Créer les données de base au démarrage
    from app.services.seed import create_demo_organization
    db = SessionLocal()
    try:
        create_demo_organization(db)
    finally:
        db.close()