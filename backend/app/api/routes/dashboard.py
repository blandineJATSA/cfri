"""
Routes du dashboard CFRI.

Endpoints :
- GET /dashboard/summary  → chiffres clés (feedbacks, CA, remboursements...)
- GET /dashboard/compute  → déclenche le calcul du scoring
- GET /problems           → top problèmes triés par impact
- GET /customers/risk     → clients à risque triés par score
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Feedback, FeedbackAnalysis, Customer,
    Order, ProblemCluster, CustomerRiskScore
)
from app.services import scoring_service

router = APIRouter(tags=["Dashboard"])

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Retourne les chiffres clés du dashboard :
    - Nombre de feedbacks analysés
    - Nombre de clients
    - CA total associé aux problèmes
    - Remboursements totaux
    - Nombre de problèmes détectés
    - Nombre de clients à risque élevé
    """
    feedbacks_count = db.query(Feedback).filter(
        Feedback.organization_id == DEMO_ORG_ID
    ).count()

    analyzed_count = (
        db.query(FeedbackAnalysis)
        .join(Feedback)
        .filter(Feedback.organization_id == DEMO_ORG_ID)
        .count()
    )

    customers_count = db.query(Customer).filter(
        Customer.organization_id == DEMO_ORG_ID
    ).count()

    # CA et remboursements totaux
    orders = db.query(Order).filter(
        Order.organization_id == DEMO_ORG_ID
    ).all()
    total_revenue = sum(o.total_amount for o in orders)
    total_refunds = sum(o.refund_amount for o in orders)

    # Problèmes détectés
    problems_count = db.query(ProblemCluster).filter(
        ProblemCluster.organization_id == DEMO_ORG_ID
    ).count()

    # Clients à risque élevé ou critique
    at_risk = (
        db.query(CustomerRiskScore)
        .join(Customer)
        .filter(
            Customer.organization_id == DEMO_ORG_ID,
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
def compute_scoring(db: Session = Depends(get_db)):
    """
    Déclenche le calcul du scoring :
    1. Calcule les problem clusters (groupes de problèmes avec impact €)
    2. Calcule les risk scores des clients
    """
    clusters = scoring_service.compute_problem_clusters(db, DEMO_ORG_ID)
    risk_scores = scoring_service.compute_customer_risk_scores(db, DEMO_ORG_ID)

    return {
        "problems_computed": len(clusters),
        "risk_scores_computed": len(risk_scores),
    }


@router.get("/problems")
def get_problems(db: Session = Depends(get_db)):
    """
    Retourne les problèmes triés par impact score décroissant.
    Ce sont les problèmes qui coûtent le plus cher à l'entreprise.
    """
    clusters = (
        db.query(ProblemCluster)
        .filter(ProblemCluster.organization_id == DEMO_ORG_ID)
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
def get_customers_at_risk(db: Session = Depends(get_db)):
    """
    Retourne les clients à risque triés par score décroissant.
    """
    scores = (
        db.query(CustomerRiskScore, Customer)
        .join(Customer, CustomerRiskScore.customer_id == Customer.id)
        .filter(Customer.organization_id == DEMO_ORG_ID)
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