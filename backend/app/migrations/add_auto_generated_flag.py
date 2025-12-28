"""
Migration: Füge is_auto_generated Spalte zu rag_chat_prompts hinzu.

CR-P2.2: Auto-Custom-Prompt-Generierung

Diese Migration fügt eine neue Spalte `is_auto_generated` zur `rag_chat_prompts` Tabelle hinzu,
um zu markieren, ob ein Custom Prompt automatisch generiert wurde oder manuell erstellt wurde.

WICHTIG: Backup wird automatisch erstellt vor Migration!
"""

import os
import sys
from pathlib import Path

# Füge Projekt-Root-Pfad hinzu
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal, engine
from backend.app.db_backup import run_migration_with_backup
from sqlalchemy import text


def migrate():
    """
    Führe Migration aus: Füge is_auto_generated Spalte hinzu.
    
    WICHTIG: Backup wird automatisch erstellt!
    """
    db_path = os.getenv("DATABASE_URL", "sqlite:///./data/qms.db")
    
    # Extrahiere DB-Pfad aus SQLite URL
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            # Relativer Pfad - relativ zum Projekt-Root
            project_root = Path(__file__).parent.parent.parent.parent
            # Entferne führenden ./ falls vorhanden
            db_path = db_path.lstrip("./")
            db_path = str(project_root / db_path)
    
    print(f"📦 Migration: Füge is_auto_generated Spalte zu rag_chat_prompts hinzu")
    print(f"📁 Datenbank: {db_path}")
    
    # Prüfe ob Spalte bereits existiert
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('rag_chat_prompts')
            WHERE name = 'is_auto_generated'
        """))
        row = result.fetchone()
        if row and row[0] > 0:
            print("✅ Spalte is_auto_generated existiert bereits - Migration übersprungen")
            return
    
    # Führe Migration mit Backup aus
    def migration_func():
        with SessionLocal() as db:
            # Füge Spalte hinzu
            db.execute(text("""
                ALTER TABLE rag_chat_prompts
                ADD COLUMN is_auto_generated BOOLEAN DEFAULT FALSE NOT NULL
            """))
            db.commit()
            print("✅ Spalte is_auto_generated erfolgreich hinzugefügt")
    
    # Backup-Verzeichnis
    backup_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "data"
    
    print(f"📦 Migration mit Backup: {db_path}")
    print(f"📁 Backup-Verzeichnis: {backup_dir}")
    
    # Führe Migration mit Backup aus
    result = run_migration_with_backup(
        db_path=db_path,
        migration_func=migration_func,
        backup_dir=backup_dir
    )
    
    if result.get('error'):
        print(f"❌ Migration fehlgeschlagen: {result.get('error')}")
        raise Exception(f"Migration fehlgeschlagen: {result.get('error')}")
    
    if result.get('migration_executed'):
        print(f"✅ Migration erfolgreich! Backup: {result.get('backup_path')}")
    else:
        print("❌ Migration wurde nicht ausgeführt")


if __name__ == "__main__":
    migrate()

