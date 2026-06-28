"""
Script de seed — crée les données de base nécessaires au fonctionnement du MVP.
Appelé automatiquement au démarrage de l'API.
"""

from sqlalchemy.orm import Session
from app.models import Organization

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"
DEMO_ORG_NAME = "Organisation Demo"
DEMO_ORG_SLUG = "demo"


def create_demo_organization(db: Session):
    """Crée l'organisation de démo si elle n'existe pas déjà."""
    existing = db.query(Organization).filter(
        Organization.id == DEMO_ORG_ID
    ).first()

    if not existing:
        org = Organization(
            id=DEMO_ORG_ID,
            name=DEMO_ORG_NAME,
            slug=DEMO_ORG_SLUG,
            plan="free",
        )
        db.add(org)
        db.commit()
        print(f"✅ Organisation demo créée : {DEMO_ORG_ID}")
    else:
        print(f"✅ Organisation demo déjà présente")