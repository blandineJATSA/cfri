"""
Middleware d'authentification Clerk — vérification JWT locale.

Clerk génère des tokens JWT signés avec une clé privée.
On vérifie ces tokens localement en récupérant la clé publique
depuis l'endpoint JWKS de Clerk (une seule fois, puis en cache).
"""

import httpx
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models import Organization, User

settings = get_settings()
security = HTTPBearer()

# URL JWKS de Clerk — contient les clés publiques pour vérifier les JWT
# Format : https://<instance>.clerk.accounts.dev/.well-known/jwks.json
# On la construit depuis la publishable key
_jwks_client = None


def get_jwks_client():
    """Retourne le client JWKS en cache."""
    global _jwks_client
    if _jwks_client is None:
        # Extraire l'instance depuis la secret key
        # La JWKS URL est dans le dashboard Clerk → Configure → API Keys
        jwks_url = settings.clerk_jwks_url
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def decode_clerk_token(token: str) -> dict:
    """
    Vérifie et décode un token JWT Clerk localement.
    Plus rapide qu'un appel API à chaque requête.
    """
    try:
        client = get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
            leeway=60,
        )
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalide : {str(e)}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Dependency FastAPI — vérifie le token et retourne le contexte utilisateur."""

    token = credentials.credentials
    payload = decode_clerk_token(token)

    # Extraire les infos du payload JWT
    # Clerk v2 met l'organisation dans le champ "o"
    clerk_user_id = payload.get("sub")
    org_data = payload.get("o", {})
    clerk_org_id = org_data.get("id") if org_data else payload.get("org_id")
    clerk_org_slug = org_data.get("slg", "") if org_data else ""
    clerk_org_name = clerk_org_slug.replace("-", " ").title() if clerk_org_slug else "Mon Organisation"
    user_email = (payload.get("email") or payload.get("primary_email_address") or "")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sans identifiant utilisateur",
        )

    # Récupérer ou créer l'organisation
    organization = None

    if clerk_org_id:
        organization = db.query(Organization).filter(
            Organization.clerk_org_id == clerk_org_id
        ).first()

        if not organization:
            slug = clerk_org_name.lower().replace(" ", "-")[:50]
            organization = Organization(
                name=clerk_org_name,
                slug=slug,
                clerk_org_id=clerk_org_id,
                plan="free",
            )
            db.add(organization)
            db.commit()
            db.refresh(organization)

    # Fallback : organisation personnelle par utilisateur
    if not organization:
        organization = db.query(Organization).filter(
            Organization.clerk_org_id == f"user_{clerk_user_id}"
        ).first()

        if not organization:
            organization = Organization(
                name=f"Organisation de {user_email or clerk_user_id}",
                slug=f"user-{clerk_user_id[:20]}",
                clerk_org_id=f"user_{clerk_user_id}",
                plan="free",
            )
            db.add(organization)
            db.commit()
            db.refresh(organization)

    # Récupérer ou créer l'utilisateur
    user = db.query(User).filter(
        User.clerk_user_id == clerk_user_id
    ).first()

    if not user:
        user = User(
            organization_id=str(organization.id),
            clerk_user_id=clerk_user_id,
            email=user_email,
        )
        db.add(user)
        db.commit()

    return {
        "user_id": str(user.id),
        "organization_id": str(organization.id),
        "clerk_user_id": clerk_user_id,
        "email": user_email,
    }