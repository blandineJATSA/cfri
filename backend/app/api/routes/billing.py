"""
Routes de facturation Stripe.

Endpoints :
- GET  /billing/plans         → liste des plans disponibles
- POST /billing/checkout      → créer une session de paiement
- POST /billing/portal        → accéder au portail client
- POST /billing/webhook       → recevoir les événements Stripe
- GET  /billing/status        → plan actuel de l'organisation
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.services.billing_service import (
    create_checkout_session,
    create_billing_portal,
    handle_webhook,
    get_plans,
)
from app.models import Organization
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/plans")
def list_plans():
    """
    Retourne les plans disponibles.
    Route publique — pas besoin d'être connecté.
    """
    return get_plans()


@router.get("/status")
async def billing_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retourne le plan actuel de l'organisation."""
    org = db.query(Organization).filter(
        Organization.id == current_user["organization_id"]
    ).first()

    return {
        "plan": org.plan if org else "free",
        "organization_id": current_user["organization_id"],
    }


@router.post("/checkout")
async def create_checkout(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée une session Stripe Checkout.
    Retourne l'URL vers laquelle rediriger l'utilisateur.
    
    Body : { "price_id": "price_xxx" }
    """
    price_id = body.get("price_id")
    if not price_id:
        raise HTTPException(status_code=400, detail="price_id requis")

    if not settings.stripe_secret_key or settings.stripe_secret_key == "":
        raise HTTPException(
            status_code=400,
            detail="Stripe non configuré"
        )

    try:
        url = create_checkout_session(
            organization_id=current_user["organization_id"],
            price_id=price_id,
            user_email=current_user.get("email", ""),
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def billing_portal(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée un lien vers le portail client Stripe.
    Permet de gérer l'abonnement, changer de plan, annuler.
    """
    org = db.query(Organization).filter(
        Organization.id == current_user["organization_id"]
    ).first()

    if not org or not org.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="Aucun abonnement actif trouvé"
        )

    try:
        url = create_billing_portal(org.stripe_customer_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        result = handle_webhook(payload, signature, db)
        return result
    except ValueError as e:
        print(f"❌ Webhook ValueError : {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"❌ Webhook Exception : {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))