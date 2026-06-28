"""
Service de gestion des jobs Redis.

Responsabilités :
- Envoyer un job d'analyse dans la file Redis
- Suivre le statut d'un job
- Retourner la progression

Un job Redis c'est une tâche mise en file d'attente.
Le worker la récupère et l'exécute en arrière-plan.
"""

from redis import Redis
from rq import Queue
from rq.job import Job
from app.config import get_settings

settings = get_settings()


def get_redis():
    """Retourne la connexion Redis."""
    return Redis.from_url(settings.redis_url)


def get_queue():
    """Retourne la file d'attente d'analyse."""
    return Queue('analysis', connection=get_redis())


def enqueue_analysis(organization_id: str, batch_size: int = 20) -> str:
    """
    Envoie un job d'analyse dans la file Redis.
    Retourne l'ID du job pour suivre sa progression.
    
    Le job sera exécuté par le worker dès qu'il est disponible.
    """
    from app.workers.analysis_worker import analyze_batch

    queue = get_queue()
    job = queue.enqueue(
        analyze_batch,
        organization_id,
        batch_size,
        job_timeout=300,  # 5 minutes max par job
        result_ttl=3600,  # Garder le résultat 1 heure
    )
    return job.id


def get_job_status(job_id: str) -> dict:
    """
    Retourne le statut d'un job Redis.
    
    Statuts possibles :
    - queued    : en attente dans la file
    - started   : en cours d'exécution
    - finished  : terminé avec succès
    - failed    : erreur
    """
    try:
        redis_conn = get_redis()
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "job_id": job_id,
            "status": job.get_status().value,
            "result": job.result,
            "error": str(job.exc_info) if job.exc_info else None,
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": str(e),
        }