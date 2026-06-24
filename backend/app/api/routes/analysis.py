"""
Route pour déclencher l'analyse IA des feedbacks.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import ai_service

router = APIRouter(prefix="/analysis", tags=["Analysis"])

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/run")
def run_analysis(db: Session = Depends(get_db)):
    """
    Analyse tous les feedbacks non encore analysés.
    Appelle l'IA pour chaque feedback et sauvegarde les résultats.
    """
    if not ai_service.settings.openai_api_key or \
       ai_service.settings.openai_api_key == "sk-REMPLACER_ICI":
        raise HTTPException(
            status_code=400,
            detail="Clé OpenAI non configurée dans le fichier .env"
        )

    result = ai_service.analyze_pending_feedbacks(db, DEMO_ORG_ID)
    return result


@router.get("/status")
def analysis_status(db: Session = Depends(get_db)):
    """
    Retourne le nombre de feedbacks analysés vs non analysés.
    """
    from app.models import Feedback, FeedbackAnalysis

    total_feedbacks = db.query(Feedback).filter(
        Feedback.organization_id == DEMO_ORG_ID
    ).count()

    analyzed = db.query(FeedbackAnalysis).join(Feedback).filter(
        Feedback.organization_id == DEMO_ORG_ID
    ).count()

    return {
        "total_feedbacks": total_feedbacks,
        "analyzed": analyzed,
        "pending": total_feedbacks - analyzed,
    }