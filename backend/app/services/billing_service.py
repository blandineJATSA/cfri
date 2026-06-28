"""
Service de facturation Stripe.

Responsabilités :
- Créer une session Stripe Checkout (page de paiement)
- Gérer les webhooks Stripe (confirmation de paiement)
- Mettre à jour le plan de l'organisation après paiement
- Créer le portail client pour gérer l'abonnement

Flux :
1. Utilisateur clique "S'abonner"
2. On crée une session Checkout Stripe
3. Stripe affiche sa page de paiement
4. Après paiement Stripe appelle notre webhook
5. On met à jour l'organisation en base
"""

import stripe
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Organization

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

# Mapping price_id → nom du plan
PRICE_TO_PLAN = {
    settings.stripe_price_starter: "starter",
    settings.stripe_price_growth: "growth",
    settings.stripe_price_business: "business",
}


def create_checkout_session(
    organization_id: str,
    price_id: str,
    user_email: str,
) -> str:
    """
    Crée une session Stripe Checkout.
    Retourne l'URL de la page de paiement Stripe.
    
    L'utilisateur est redirigé vers cette URL pour payer.
    Après paiement, Stripe le redirige vers notre dashboard.
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        customer_email=user_email if user_email else None,
        # Métadonnées pour retrouver l'organisation après paiement
        metadata={
            "organization_id": organization_id,
        },
        # URLs de redirection après paiement
        success_url=f"{settings.frontend_url}/dashboard?payment=success",
        cancel_url=f"{settings.frontend_url}/settings?payment=cancelled",
    )
    return session.url


def create_billing_portal(stripe_customer_id: str) -> str:
    """
    Crée un lien vers le portail client Stripe.
    Permet à l'utilisateur de gérer son abonnement,
    changer de plan, ou annuler.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/settings",
    )
    return session.url


def handle_webhook(payload: bytes, signature: str, db: Session) -> dict:
    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
            tolerance=300,
        )
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Signature webhook invalide : {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur webhook : {str(e)}")

    # Nouveau SDK Stripe — accès par attributs, pas par dict
    event_type = event.type

    if event_type == "checkout.session.completed":
        session_obj = event.data.object
        metadata = session_obj.metadata
        organization_id = metadata["organization_id"] if metadata and "organization_id" in metadata else None
        subscription_id = session_obj.subscription
        stripe_customer_id = session_obj.customer

        if organization_id and subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                price_id = subscription.items.data[0].price.id
                plan = PRICE_TO_PLAN.get(price_id, "starter")

                org = db.query(Organization).filter(
                    Organization.id == organization_id
                ).first()

                if org:
                    org.plan = plan
                    org.stripe_customer_id = stripe_customer_id
                    org.stripe_subscription_id = subscription_id
                    db.commit()
                    print(f"✅ Plan mis à jour : {plan} pour org {organization_id}")
            except Exception as e:
                print(f"❌ Erreur mise à jour plan : {e}")

    elif event_type == "customer.subscription.deleted":
        subscription = event.data.object
        customer_id = subscription.customer

        org = db.query(Organization).filter(
            Organization.stripe_customer_id == customer_id
        ).first()

        if org:
            org.plan = "free"
            org.stripe_subscription_id = None
            db.commit()

    return {"status": "ok", "type": event_type}


def get_plans():
    """Retourne les plans disponibles avec leurs prix."""
    return [
        {
            "id": "starter",
            "name": "Starter",
            "price": 99,
            "currency": "EUR",
            "price_id": settings.stripe_price_starter,
            "features": [
                "500 feedbacks / mois",
                "1 utilisateur",
                "Dashboard complet",
                "Rapports hebdomadaires",
            ],
        },
        {
            "id": "growth",
            "name": "Growth",
            "price": 249,
            "currency": "EUR",
            "price_id": settings.stripe_price_growth,
            "features": [
                "5 000 feedbacks / mois",
                "5 utilisateurs",
                "Connecteur Shopify",
                "Export CSV/PDF",
                "Support prioritaire",
            ],
        },
        {
            "id": "business",
            "name": "Business",
            "price": 499,
            "currency": "EUR",
            "price_id": settings.stripe_price_business,
            "features": [
                "Feedbacks illimités",
                "Utilisateurs illimités",
                "Tous les connecteurs",
                "API access",
                "Customer success dédié",
            ],
        },
    ]