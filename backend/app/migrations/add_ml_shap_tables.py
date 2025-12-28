"""
Migration: ML/SHAP SQLite-Persistenz Tabellen

Erstellt die 3 neuen Tabellen für ML/SHAP-Persistenz:
- training_samples
- shap_background_data
- shap_cache

Version: 2.7.0
Stand: 2025-11-14
"""

import os
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Jetzt können wir die Imports machen
from app.database import engine, Base
from app.models import (
    TrainingSampleModel,
    SHAPBackgroundDataModel,
    SHAPCacheEntryModel
)


def migrate():
    """
    Führe Migration aus: Erstelle 3 neue Tabellen.
    
    Features:
    - training_samples: Training-Daten für ML-Modelle
    - shap_background_data: Historische Search-Daten für SHAP
    - shap_cache: Gecachte SHAP-Erklärungen
    """
    print("🔄 Starte Migration: ML/SHAP SQLite-Persistenz Tabellen")
    
    try:
        # Erstelle Tabellen (checkfirst=True macht Migration idempotent)
        print("  📊 Erstelle training_samples Tabelle...")
        TrainingSampleModel.__table__.create(bind=engine, checkfirst=True)
        
        print("  📊 Erstelle shap_background_data Tabelle...")
        SHAPBackgroundDataModel.__table__.create(bind=engine, checkfirst=True)
        
        print("  📊 Erstelle shap_cache Tabelle...")
        SHAPCacheEntryModel.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Migration erfolgreich abgeschlossen")
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        raise


if __name__ == '__main__':
    """
    Führe Migration mit automatischem Backup aus.
    
    Usage:
        python -m backend.app.migrations.add_ml_shap_tables
    """
    from app.db_backup import run_migration_with_backup
    
    # DB-Pfad aus DATABASE_URL extrahieren
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/qms.db")
    
    # Konvertiere sqlite:///data/qms.db zu /absoluter/pfad/data/qms.db
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        # Wenn relativer Pfad, mache absolut
        if not os.path.isabs(db_path):
            # Nehme Projekt-Root als Basis
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / db_path)
    else:
        # Fallback
        db_path = "data/qms.db"
        if not os.path.isabs(db_path):
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / db_path)
    
    # Backup-Verzeichnis
    backup_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "data"
    
    print(f"📦 Migration mit Backup: {db_path}")
    print(f"📁 Backup-Verzeichnis: {backup_dir}")
    
    # Führe Migration mit Backup aus
    result = run_migration_with_backup(
        db_path=db_path,
        migration_func=migrate,
        backup_dir=backup_dir
    )
    
    # Prüfe Result
    if result.get('error'):
        print(f"❌ Migration fehlgeschlagen: {result['error']}")
        sys.exit(1)
    elif not result.get('migration_executed'):
        print("❌ Migration wurde nicht ausgeführt")
        sys.exit(1)
    else:
        print(f"✅ Migration erfolgreich! Backup: {result.get('backup_path')}")
        sys.exit(0)

