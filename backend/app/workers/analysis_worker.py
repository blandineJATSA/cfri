"""
Worker Redis — analyse les feedbacks en arrière-plan.

Ce fichier tourne comme un processus séparé.
Il écoute la file d'attente Redis et traite les jobs d'analyse.

Démarrer le worker :
    python -m app.workers.analysis_worker

Le worker reçoit un job contenant :
- organization_id : l'organisation à analyser
- batch_size : nombre de feedbacks à analyser par job
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from redis import Redis
from rq import Worker, Queue
from app.config import get_settings

settings = get_settings()


def analyze_batch(organization_id: str, batch_size: int = 20):
    """
    Fonction exécutée par le worker.
    Analyse un batch de feedbacks pour une organisation.
    
    Cette fonction tourne dans le processus worker,
    pas dans l'API FastAPI.
    """
    from app.database import SessionLocal
    from app.services.ai_service import analyze_pending_feedbacks

    db = SessionLocal()
    try:
        result = analyze_pending_feedbacks(db, organization_id, limit=batch_size)
        return result
    finally:
        db.close()


def get_queue():
    """Retourne la file d'attente Redis."""
    redis_conn = Redis.from_url(settings.redis_url)
    return Queue('analysis', connection=redis_conn)


if __name__ == "__main__":
    """Démarrer le worker en ligne de commande."""
    from rq.worker import SimpleWorker
    redis_conn = Redis.from_url(settings.redis_url)
    queue = Queue('analysis', connection=redis_conn)
    worker = SimpleWorker([queue], connection=redis_conn)
    print(f"🔧 Worker démarré — écoute la queue 'analysis'")
    print(f"   Redis : {settings.redis_url}")
    worker.work()