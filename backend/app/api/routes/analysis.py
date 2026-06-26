from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import ai_service
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/run")
async def run_analysis(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not ai_service.settings.openai_api_key or \
       ai_service.settings.openai_api_key == "sk-REMPLACER_ICI":
        raise HTTPException(
            status_code=400,
            detail="Clé OpenAI non configurée"
        )
    result = ai_service.analyze_pending_feedbacks(
        db, current_user["organization_id"], limit=20
    )
    return result


@router.get("/status")
async def analysis_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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