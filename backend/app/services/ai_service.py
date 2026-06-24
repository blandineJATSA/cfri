"""
Service d'analyse IA des feedbacks.

Responsabilités :
- Charger le prompt depuis le fichier texte
- Appeler l'API OpenAI avec le feedback
- Valider et parser la réponse JSON
- Sauvegarder l'analyse en base de données
"""

import os
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import (
    Feedback, FeedbackAnalysis,
    SentimentEnum, UrgencyEnum
)

settings = get_settings()

# Chemin vers le fichier de prompt
PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "prompts",
    "feedback_analysis.txt"
)


def load_prompt() -> str:
    """Charge le prompt depuis le fichier texte."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def analyze_feedback_text(feedback_text: str) -> dict:
    """
    Envoie un feedback à OpenAI et retourne l'analyse structurée.
    
    Retourne un dictionnaire avec :
    category, subcategory, sentiment, urgency,
    root_cause, customer_intent, summary,
    recommended_action, confidence
    """
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Charger le prompt et injecter le feedback
    prompt = load_prompt().replace("{feedback_text}", feedback_text)
    
    response = client.chat.completions.create(
        model=settings.ai_model,
        messages=[
            {
                "role": "system",
                "content": "Tu es un expert en analyse de feedback client. Réponds uniquement en JSON valide."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,  # Basse température = réponses plus cohérentes
        max_tokens=500,
    )
    
    # Extraire le texte de la réponse
    raw_text = response.choices[0].message.content.strip()
    
    # Nettoyer si OpenAI ajoute des backticks markdown
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    
    # Parser le JSON
    result = json.loads(raw_text)
    return result


def save_analysis(db: Session, feedback: Feedback, analysis: dict) -> FeedbackAnalysis:
    """
    Sauvegarde l'analyse IA en base de données.
    Valide les enums avant insertion.
    """
    # Valider le sentiment
    sentiment = analysis.get("sentiment", "neutral")
    if sentiment not in ["positive", "neutral", "negative"]:
        sentiment = "neutral"

    # Valider l'urgence
    urgency = analysis.get("urgency", "low")
    if urgency not in ["low", "medium", "high", "critical"]:
        urgency = "low"

    feedback_analysis = FeedbackAnalysis(
        feedback_id=feedback.id,
        category=analysis.get("category", "other"),
        subcategory=analysis.get("subcategory"),
        sentiment=SentimentEnum(sentiment),
        urgency=UrgencyEnum(urgency),
        root_cause=analysis.get("root_cause"),
        customer_intent=analysis.get("customer_intent"),
        summary=analysis.get("summary"),
        recommended_action=analysis.get("recommended_action"),
        confidence=float(analysis.get("confidence", 0.8)),
        model_name=settings.ai_model,
    )
    db.add(feedback_analysis)
    db.commit()
    db.refresh(feedback_analysis)
    return feedback_analysis


def analyze_pending_feedbacks(db: Session, organization_id: str) -> dict:
    """
    Analyse tous les feedbacks qui n'ont pas encore été analysés.
    Retourne un résumé : combien analysés, combien en erreur.
    """
    # Récupérer les feedbacks sans analyse
    feedbacks_to_analyze = (
        db.query(Feedback)
        .outerjoin(FeedbackAnalysis)
        .filter(
            Feedback.organization_id == organization_id,
            FeedbackAnalysis.id == None  # Pas encore analysé
        )
        .all()
    )

    total = len(feedbacks_to_analyze)
    success = 0
    errors = 0

    print(f"📊 {total} feedbacks à analyser...")

    for i, feedback in enumerate(feedbacks_to_analyze):
        try:
            print(f"  [{i+1}/{total}] Analyse: {feedback.body[:60]}...")
            
            # Appel à l'IA
            analysis = analyze_feedback_text(feedback.body)
            
            # Sauvegarde
            save_analysis(db, feedback, analysis)
            success += 1

        except Exception as e:
            print(f"  ❌ Erreur sur feedback {feedback.id}: {str(e)}")
            errors += 1
            continue

    print(f"✅ Analyse terminée — {success} réussis, {errors} erreurs")

    return {
        "total": total,
        "success": success,
        "errors": errors,
    }