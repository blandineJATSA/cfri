from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Feedback, FeedbackAnalysis, Customer,
    Order, ProblemCluster, CustomerRiskScore
)
from app.services import scoring_service
from app.middleware.auth import get_current_user

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["organization_id"]

    feedbacks_count = db.query(Feedback).filter(
        Feedback.organization_id == org_id
    ).count()

    analyzed_count = (
        db.query(FeedbackAnalysis)
        .join(Feedback)
        .filter(Feedback.organization_id == org_id)
        .count()
    )

    customers_count = db.query(Customer).filter(
        Customer.organization_id == org_id
    ).count()

    orders = db.query(Order).filter(Order.organization_id == org_id).all()
    total_revenue = sum(o.total_amount for o in orders)
    total_refunds = sum(o.refund_amount for o in orders)

    problems_count = db.query(ProblemCluster).filter(
        ProblemCluster.organization_id == org_id
    ).count()

    at_risk = (
        db.query(CustomerRiskScore)
        .join(Customer)
        .filter(
            Customer.organization_id == org_id,
            CustomerRiskScore.risk_level.in_(["high", "critical"]),
        )
        .count()
    )

    return {
        "feedbacks_count": feedbacks_count,
        "analyzed_count": analyzed_count,
        "customers_count": customers_count,
        "total_revenue": round(total_revenue, 2),
        "total_refunds": round(total_refunds, 2),
        "problems_count": problems_count,
        "at_risk_customers": at_risk,
    }


@router.post("/dashboard/compute")
async def compute_scoring(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["organization_id"]
    clusters = scoring_service.compute_problem_clusters(db, org_id)
    risk_scores = scoring_service.compute_customer_risk_scores(db, org_id)
    return {
        "problems_computed": len(clusters),
        "risk_scores_computed": len(risk_scores),
    }


@router.get("/problems")
async def get_problems(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    clusters = (
        db.query(ProblemCluster)
        .filter(ProblemCluster.organization_id == current_user["organization_id"])
        .order_by(ProblemCluster.impact_score.desc())
        .all()
    )
    return [
        {
            "id": str(c.id),
            "category": c.category,
            "subcategory": c.subcategory,
            "title": c.title,
            "feedback_count": c.feedback_count,
            "customers_count": c.customers_count,
            "associated_revenue": c.associated_revenue,
            "refund_amount": c.refund_amount,
            "negative_rate": round(c.negative_rate * 100, 1),
            "impact_score": c.impact_score,
        }
        for c in clusters
    ]


@router.get("/customers/risk")
async def get_customers_at_risk(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    scores = (
        db.query(CustomerRiskScore, Customer)
        .join(Customer, CustomerRiskScore.customer_id == Customer.id)
        .filter(Customer.organization_id == current_user["organization_id"])
        .order_by(CustomerRiskScore.risk_score.desc())
        .all()
    )
    return [
        {
            "customer_id": str(customer.id),
            "email": customer.email,
            "name": customer.name,
            "total_spent": customer.total_spent,
            "orders_count": customer.orders_count,
            "risk_score": score.risk_score,
            "risk_level": score.risk_level.value,
            "reasons": score.reasons,
            "recommended_action": score.recommended_action,
        }
        for score, customer in scores
    ]