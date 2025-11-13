"""
Celery App für RAG Background Jobs.

Infrastructure Layer: Celery-Konfiguration für asynchrone SHAP-Berechnungen.

TDD Phase 2: GREEN - Minimale Celery-App-Implementierung.
"""

from celery import Celery
import os


# Celery App (Singleton)
celery_app = Celery(
    'documind_rag_worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# Celery Konfiguration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Berlin',
    enable_utc=True,
    
    # Task Tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Task Time Limits
    task_time_limit=120,  # 2 Minuten Hard Limit
    task_soft_time_limit=100,  # 100s Soft Limit
    
    # Result Backend
    result_expires=3600,  # Ergebnisse für 1 Stunde speichern
    result_persistent=True,
    
    # Worker
    worker_prefetch_multiplier=1,  # Ein Task pro Worker (für SHAP-Performance)
    worker_max_tasks_per_child=50,  # Worker nach 50 Tasks neu starten
    
    # Routing
    task_routes={
        'ragintegration.compute_shap_explanation': {
            'queue': 'shap_queue',
            'routing_key': 'shap.compute'
        }
    }
)

# Health Check Task (für Monitoring)
@celery_app.task(name='celery.ping')
def ping():
    """Simple Ping-Task für Health Check."""
    return 'pong'


# Importiere Tasks explizit (für Auto-Discovery)
# WICHTIG: Import nach celery_app Definition, um zirkuläre Imports zu vermeiden
def _import_tasks():
    """Importiere Tasks explizit für Registrierung."""
    try:
        from . import tasks  # noqa: F401
    except ImportError:
        pass  # Tasks noch nicht vorhanden


# Registriere Tasks
_import_tasks()

