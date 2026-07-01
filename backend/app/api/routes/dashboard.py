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

# ── Données demo pour l'onboarding ──────────────────────────────────────────

DEMO_SUMMARY = {
    "feedbacks_count": 532,
    "analyzed_count": 532,
    "customers_count": 30,
    "total_revenue": 237874.0,
    "total_refunds": 11617.0,
    "problems_count": 40,
    "at_risk_customers": 29,
    "is_demo": True,
}

DEMO_PROBLEMS = [
    {
        "id": "demo-1",
        "category": "delivery",
        "subcategory": "late_delivery",
        "title": "Problèmes de livraison — late delivery",
        "feedback_count": 97,
        "customers_count": 18,
        "associated_revenue": 87420.0,
        "refund_amount": 4200.0,
        "negative_rate": 100.0,
        "impact_score": 315.29,
        "is_demo": True,
    },
    {
        "id": "demo-2",
        "category": "product_quality",
        "subcategory": "damaged_item",
        "title": "Qualité produit — damaged item",
        "feedback_count": 36,
        "customers_count": 8,
        "associated_revenue": 32800.0,
        "refund_amount": 2100.0,
        "negative_rate": 100.0,
        "impact_score": 160.57,
        "is_demo": True,
    },
    {
        "id": "demo-3",
        "category": "refund",
        "subcategory": "delayed_refund",
        "title": "Remboursements et retours — delayed refund",
        "feedback_count": 24,
        "customers_count": 6,
        "associated_revenue": 18600.0,
        "refund_amount": 3800.0,
        "negative_rate": 100.0,
        "impact_score": 138.47,
        "is_demo": True,
    },
    {
        "id": "demo-4",
        "category": "product_quality",
        "subcategory": "poor_quality",
        "title": "Qualité produit — poor quality",
        "feedback_count": 24,
        "customers_count": 6,
        "associated_revenue": 14400.0,
        "refund_amount": 890.0,
        "negative_rate": 100.0,
        "impact_score": 127.35,
        "is_demo": True,
    },
    {
        "id": "demo-5",
        "category": "customer_service",
        "subcategory": "no_response",
        "title": "Service client — no response",
        "feedback_count": 19,
        "customers_count": 5,
        "associated_revenue": 12300.0,
        "refund_amount": 0.0,
        "negative_rate": 100.0,
        "impact_score": 113.86,
        "is_demo": True,
    },
]


def is_empty_organization(db: Session, org_id: str) -> bool:
    """Retourne True si l'organisation n'a aucun feedback importé."""
    count = db.query(Feedback).filter(
        Feedback.organization_id == org_id
    ).count()
    return count == 0


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["organization_id"]

    # Onboarding — organisation vide → données demo
    if is_empty_organization(db, org_id):
        return DEMO_SUMMARY

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
        "is_demo": False,
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
    org_id = current_user["organization_id"]

    # Onboarding — organisation vide → problèmes demo
    if is_empty_organization(db, org_id):
        return DEMO_PROBLEMS

    clusters = (
        db.query(ProblemCluster)
        .filter(ProblemCluster.organization_id == org_id)
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
            "is_demo": False,
        }
        for c in clusters
    ]


@router.get("/customers/risk")
async def get_customers_at_risk(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["organization_id"]

    scores = (
        db.query(CustomerRiskScore, Customer)
        .join(Customer, CustomerRiskScore.customer_id == Customer.id)
        .filter(Customer.organization_id == org_id)
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