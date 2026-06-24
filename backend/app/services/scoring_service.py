"""
Service de scoring — calcule l'impact revenue des problèmes
et le risk score des clients.

Deux fonctions principales :
- compute_problem_clusters : groupe les feedbacks par catégorie
  et calcule l'impact financier de chaque problème
- compute_customer_risk_scores : calcule le risque de churn
  pour chaque client
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import (
    Feedback, FeedbackAnalysis, Customer, Order,
    ProblemCluster, CustomerRiskScore, RiskLevel
)


def compute_problem_clusters(db: Session, organization_id: str) -> list:
    """
    Groupe les feedbacks analysés par catégorie et calcule
    l'impact revenue de chaque problème.

    Pour chaque catégorie de problème on calcule :
    - Nombre de feedbacks
    - Nombre de clients uniques touchés
    - CA associé (commandes des clients qui ont eu ce problème)
    - Remboursements associés
    - Taux de sentiment négatif
    - Score d'impact composite
    """

    # Récupérer toutes les analyses avec leur feedback et client
    analyses = (
        db.query(FeedbackAnalysis, Feedback)
        .join(Feedback, FeedbackAnalysis.feedback_id == Feedback.id)
        .filter(Feedback.organization_id == organization_id)
        .all()
    )

    if not analyses:
        return []

    # Grouper par catégorie
    clusters = {}
    for analysis, feedback in analyses:
        category = analysis.category or "other"
        subcategory = analysis.subcategory or ""

        key = f"{category}|{subcategory}"

        if key not in clusters:
            clusters[key] = {
                "category": category,
                "subcategory": subcategory,
                "feedback_ids": [],
                "customer_ids": set(),
                "negative_count": 0,
                "urgency_scores": [],
            }

        clusters[key]["feedback_ids"].append(feedback.id)

        if feedback.customer_id:
            clusters[key]["customer_ids"].add(str(feedback.customer_id))

        if analysis.sentiment and analysis.sentiment.value == "negative":
            clusters[key]["negative_count"] += 1

        urgency_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if analysis.urgency:
            clusters[key]["urgency_scores"].append(
                urgency_map.get(analysis.urgency.value, 1)
            )

    # Supprimer les anciens clusters de cette organisation
    db.query(ProblemCluster).filter(
        ProblemCluster.organization_id == organization_id
    ).delete()
    db.commit()

    results = []

    for key, data in clusters.items():
        feedback_count = len(data["feedback_ids"])
        customers_count = len(data["customer_ids"])

        # Calculer le CA associé aux clients touchés
        associated_revenue = 0.0
        refund_amount = 0.0

        if data["customer_ids"]:
            orders = (
                db.query(Order)
                .filter(
                    Order.organization_id == organization_id,
                    Order.customer_id.in_(list(data["customer_ids"])),
                )
                .all()
            )
            associated_revenue = sum(o.total_amount for o in orders)
            refund_amount = sum(o.refund_amount for o in orders)

        # Taux de sentiment négatif
        negative_rate = data["negative_count"] / feedback_count if feedback_count > 0 else 0

        # Score d'urgence moyen
        avg_urgency = (
            sum(data["urgency_scores"]) / len(data["urgency_scores"])
            if data["urgency_scores"] else 1
        )

        # Score d'impact composite
        # Formule : volume + impact revenue + remboursements + sentiment + urgence
        impact_score = (
            feedback_count * 1.0
            + associated_revenue * 0.001
            + refund_amount * 0.005
            + negative_rate * 20
            + avg_urgency * 10
        )

        # Titre lisible pour le problème
        title_map = {
            "delivery": "Problèmes de livraison",
            "product_quality": "Qualité produit",
            "refund": "Remboursements et retours",
            "customer_service": "Service client",
            "pricing": "Prix et frais",
            "website": "Site web",
            "stock": "Disponibilité produit",
            "other": "Autres problèmes",
        }
        title = title_map.get(data["category"], data["category"].replace("_", " ").title())
        if data["subcategory"]:
            title = f"{title} — {data['subcategory'].replace('_', ' ')}"

        # Créer le cluster en base
        cluster = ProblemCluster(
            organization_id=organization_id,
            category=data["category"],
            subcategory=data["subcategory"] or None,
            title=title,
            feedback_count=feedback_count,
            customers_count=customers_count,
            associated_revenue=round(associated_revenue, 2),
            refund_amount=round(refund_amount, 2),
            negative_rate=round(negative_rate, 3),
            impact_score=round(impact_score, 2),
        )
        db.add(cluster)
        results.append(cluster)

    db.commit()
    for r in results:
        db.refresh(r)

    # Trier par impact score décroissant
    results.sort(key=lambda x: x.impact_score, reverse=True)
    return results


def compute_customer_risk_scores(db: Session, organization_id: str) -> list:
    """
    Calcule le risk score pour chaque client.

    Facteurs pris en compte :
    - Nombre de feedbacks négatifs récents (30 derniers jours)
    - Montant total dépensé (les gros clients sont plus risqués à perdre)
    - Présence de remboursements récents
    - Note moyenne basse
    """

    customers = (
        db.query(Customer)
        .filter(Customer.organization_id == organization_id)
        .all()
    )

    # Supprimer les anciens scores
    # On récupère d'abord les IDs des clients de cette org
    customer_ids = [c.id for c in customers]
    if customer_ids:
        db.query(CustomerRiskScore).filter(
            CustomerRiskScore.customer_id.in_(customer_ids)
        ).delete(synchronize_session=False)
        db.commit()

    results = []
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    for customer in customers:
        risk_score = 0.0
        reasons = []

        # Feedbacks récents négatifs
        recent_negative = (
            db.query(FeedbackAnalysis)
            .join(Feedback)
            .filter(
                Feedback.customer_id == customer.id,
                Feedback.created_at >= thirty_days_ago,
                FeedbackAnalysis.sentiment == "negative",
            )
            .count()
        )

        if recent_negative >= 3:
            risk_score += 40
            reasons.append(f"{recent_negative} feedbacks négatifs en 30 jours")
        elif recent_negative == 2:
            risk_score += 25
            reasons.append(f"{recent_negative} feedbacks négatifs en 30 jours")
        elif recent_negative == 1:
            risk_score += 15
            reasons.append("1 feedback négatif récent")

        # Remboursements récents
        recent_refunds = (
            db.query(Order)
            .filter(
                Order.customer_id == customer.id,
                Order.refund_amount > 0,
                Order.created_at >= thirty_days_ago,
            )
            .count()
        )

        if recent_refunds > 0:
            risk_score += 20
            reasons.append(f"{recent_refunds} remboursement(s) récent(s)")

        # Note moyenne basse
        avg_rating = (
            db.query(func.avg(Feedback.rating))
            .filter(
                Feedback.customer_id == customer.id,
                Feedback.rating.isnot(None),
            )
            .scalar()
        )

        if avg_rating and avg_rating < 2.5:
            risk_score += 20
            reasons.append(f"Note moyenne de {round(avg_rating, 1)}/5")
        elif avg_rating and avg_rating < 3.5:
            risk_score += 10
            reasons.append(f"Note moyenne de {round(avg_rating, 1)}/5")

        # Valeur client élevée = risque business plus important
        if customer.total_spent and customer.total_spent > 500:
            risk_score += 10
            reasons.append(f"Client VIP ({round(customer.total_spent)}€ dépensés)")

        # Déterminer le niveau de risque
        if risk_score >= 60:
            risk_level = RiskLevel.critical
        elif risk_score >= 40:
            risk_level = RiskLevel.high
        elif risk_score >= 20:
            risk_level = RiskLevel.medium
        else:
            risk_level = RiskLevel.low

        # Action recommandée
        if risk_level in [RiskLevel.critical, RiskLevel.high]:
            recommended_action = "Contacter ce client en priorité et proposer un geste commercial"
        elif risk_level == RiskLevel.medium:
            recommended_action = "Surveiller ce client et répondre rapidement à ses prochains feedbacks"
        else:
            recommended_action = "Aucune action urgente requise"

        score = CustomerRiskScore(
            customer_id=customer.id,
            risk_score=round(risk_score, 1),
            risk_level=risk_level,
            reasons=reasons if reasons else ["Aucun problème détecté"],
            recommended_action=recommended_action,
        )
        db.add(score)
        results.append(score)

    db.commit()
    return results