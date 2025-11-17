#!/usr/bin/env python3
"""
LTR Model Training Script.

Trainiert ein Learning-to-Rank Modell aus SQLite Training-Daten.

Usage:
    python scripts/train_ltr_model.py
    
Hinweis: Benötigt scikit-learn (und optional lightgbm).
Installation: pip install scikit-learn lightgbm
"""

import os
import sys
from pathlib import Path

# Prüfe Dependencies
try:
    import sklearn
except ImportError:
    print("❌ scikit-learn nicht gefunden!")
    print("   Installation: pip install scikit-learn")
    sys.exit(1)

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Docker-Container: /app ist Working-Directory, Code ist direkt unter /app
# Lokal: Code ist unter backend/app
try:
    # Versuche Docker-Container-Import (app.database)
    from app.database import SessionLocal
except ImportError:
    # Fallback: Lokaler Import (backend.app.database)
    from backend.app.database import SessionLocal
from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
    TrainingDataRepositorySQLite
)
from contexts.ragintegration.infrastructure.ml.training_pipeline import (
    LTRTrainingPipeline
)


def train_ltr_model():
    """
    Trainiere LTR-Modell aus SQLite Training-Daten.
    
    Returns:
        True wenn erfolgreich
    """
    print("🤖 Starte LTR-Modell Training...")
    
    # DB-Session
    db_session = SessionLocal()
    
    try:
        # Repository
        training_repo = TrainingDataRepositorySQLite(db_session)
        
        # Prüfe ob Training-Daten vorhanden sind
        stats = training_repo.get_statistics()
        total_samples = stats.get('total_samples', 0)
        
        if total_samples == 0:
            print("❌ Keine Training-Daten gefunden!")
            print("   Bitte erstelle zuerst Training-Samples (z.B. durch Feedback im RAG-Chat)")
            return False
        
        print(f"✅ {total_samples} Training-Samples gefunden")
        print(f"   Ältestes Sample: {stats.get('oldest_sample', 'N/A')}")
        print(f"   Neuestes Sample: {stats.get('newest_sample', 'N/A')}")
        print(f"   Eindeutige Queries: {stats.get('unique_queries', 0)}")
        
        # Training Pipeline
        pipeline = LTRTrainingPipeline(
            training_data_repo=training_repo,
            model_type='lightgbm',
            model_version='1.0.0'
        )
        
        # Trainiere mit Cross-Validation
        print("\n🔄 Trainiere Modell mit Cross-Validation...")
        validation_scores = pipeline.train_and_validate(
            n_splits=3,
            num_boost_round=100,
            learning_rate=0.1,
            max_depth=6,
            num_leaves=31
        )
        
        print(f"\n✅ Training abgeschlossen!")
        print(f"   NDCG Mean: {validation_scores['ndcg_mean']:.4f}")
        print(f"   NDCG Std: {validation_scores['ndcg_std']:.4f}")
        print(f"   NDCG Scores: {validation_scores['ndcg_scores']}")
        
        # Speichere Modell (FIX 3: Relativer Pfad für Docker-Container)
        # Verwende 'data/ml_models/ltr_ranker_v1.pkl' (relativ zu project_root)
        model_dir = project_root / 'data' / 'ml_models'
        model_path = model_dir / 'ltr_ranker_v1.pkl'
        print(f"\n💾 Speichere Modell nach: {model_path}")
        
        # Erstelle Verzeichnis falls nicht vorhanden
        model_dir.mkdir(parents=True, exist_ok=True)
        
        pipeline.save_model(str(model_path))
        
        print(f"✅ Modell erfolgreich gespeichert!")
        print(f"   Pfad: {model_path}")
        print(f"   Größe: {model_path.stat().st_size / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Training: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db_session.close()


if __name__ == '__main__':
    success = train_ltr_model()
    sys.exit(0 if success else 1)

