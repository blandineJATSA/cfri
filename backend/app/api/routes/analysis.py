"""
Routes d'analyse IA — version avec worker Redis.

Au lieu d'analyser directement dans l'API (qui bloque),
on envoie un job dans Redis et on répond immédiatement.
Le worker tourne en arrière-plan et fait le vrai travail.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import ai_service
from app.services.job_service import enqueue_analysis, get_job_status
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/run")
async def run_analysis(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lance l'analyse IA en arrière-plan via Redis.
    Répond immédiatement avec un job_id.
    Le frontend poll /analysis/job/{job_id} pour suivre la progression.
    """
    if not ai_service.settings.openai_api_key or \
       ai_service.settings.openai_api_key == "sk-REMPLACER_ICI":
        raise HTTPException(
            status_code=400,
            detail="Clé OpenAI non configurée"
        )

    org_id = current_user["organization_id"]

    # Vérifier s'il reste des feedbacks à analyser
    from app.models import Feedback, FeedbackAnalysis
    pending = (
        db.query(Feedback)
        .outerjoin(FeedbackAnalysis)
        .filter(
            Feedback.organization_id == org_id,
            FeedbackAnalysis.id == None
        )
        .count()
    )

    if pending == 0:
        return {
            "status": "nothing_to_analyze",
            "message": "Tous les feedbacks sont déjà analysés",
            "pending": 0,
        }

    # Envoyer le job dans Redis
    try:
        job_id = enqueue_analysis(org_id, batch_size=20)
        return {
            "status": "queued",
            "job_id": job_id,
            "pending": pending,
            "message": f"Job créé — {min(20, pending)} feedbacks en cours d'analyse",
        }
    except Exception as e:
        # Si Redis n'est pas disponible, fallback sur l'analyse directe
        result = ai_service.analyze_pending_feedbacks(db, org_id, limit=20)
        return {
            "status": "completed",
            "job_id": None,
            **result,
        }


@router.get("/job/{job_id}")
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Retourne le statut d'un job d'analyse.
    Le frontend appelle cet endpoint toutes les 3 secondes.
    """
    return get_job_status(job_id)


@router.get("/status")
async def analysis_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retourne le nombre de feedbacks analysés vs en attente."""
    from app.models import Feedback, FeedbackAnalysis

    total = db.query(Feedback).filter(
        Feedback.organization_id == current_user["organization_id"]
    ).count()

    analyzed = db.query(FeedbackAnalysis).join(Feedback).filter(
        Feedback.organization_id == current_user["organization_id"]
    ).count()

    return {
        "total_feedbacks": total,
        "analyzed": analyzed,
        "pending": total - analyzed,
    }