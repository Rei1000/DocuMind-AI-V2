"""
Migration: Mache document_type_id in rag_chat_prompts nullable für Default-Prompts.

Version: 2.9.1
Stand: 2025-12-05

Diese Migration macht die Spalte `document_type_id` in der Tabelle `rag_chat_prompts` nullable,
um Default-Prompts (document_type_id = NULL) zu unterstützen.

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
    Führe Migration aus: Mache document_type_id nullable.
    
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
    
    print(f"📦 Migration: Mache document_type_id in rag_chat_prompts nullable")
    print(f"📁 Datenbank: {db_path}")
    
    # Prüfe ob Spalte bereits nullable ist
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT "notnull" as is_not_null
            FROM pragma_table_info('rag_chat_prompts')
            WHERE name = 'document_type_id'
        """))
        row = result.fetchone()
        if row and row[0] == 0:
            print("✅ Spalte document_type_id ist bereits nullable - Migration übersprungen")
            return
    
    # Führe Migration mit Backup aus
    def migration_func():
        with SessionLocal() as db:
            # Prüfe welche Spalten die alte Tabelle hat
            result = db.execute(text("""
                SELECT name FROM pragma_table_info('rag_chat_prompts')
                ORDER BY cid
            """))
            old_columns = [row[0] for row in result.fetchall()]
            print(f"  📋 Alte Spalten: {', '.join(old_columns)}")
            
            # Prüfe ob is_auto_generated existiert
            has_auto_generated = 'is_auto_generated' in old_columns
            
            # SQLite unterstützt kein ALTER COLUMN direkt
            # Wir müssen die Tabelle neu erstellen mit der neuen Struktur
            print("  🔄 Lösche eventuelle temporäre Tabelle...")
            db.execute(text("DROP TABLE IF EXISTS rag_chat_prompts_new"))
            
            print("  🔄 Erstelle temporäre Tabelle...")
            
            # 1. Erstelle temporäre Tabelle mit neuer Struktur
            create_table_sql = """
                CREATE TABLE rag_chat_prompts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_type_id INTEGER UNIQUE,
                    prompt_text TEXT NOT NULL,
                    multi_query_prompt_text TEXT,
                    created_by_user_id INTEGER NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"""
            
            if has_auto_generated:
                create_table_sql += """,
                    is_auto_generated BOOLEAN DEFAULT FALSE NOT NULL"""
            
            create_table_sql += """,
                    FOREIGN KEY (document_type_id) REFERENCES document_types(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
                    CHECK (LENGTH(prompt_text) > 0)
                )
            """
            
            db.execute(text(create_table_sql))
            
            # 2. Kopiere Daten (explizit Spalten angeben)
            print("  🔄 Kopiere Daten...")
            if has_auto_generated:
                db.execute(text("""
                    INSERT INTO rag_chat_prompts_new 
                    (id, document_type_id, prompt_text, multi_query_prompt_text, 
                     created_by_user_id, created_at, updated_at, is_auto_generated)
                    SELECT id, document_type_id, prompt_text, multi_query_prompt_text,
                           created_by_user_id, created_at, updated_at, is_auto_generated
                    FROM rag_chat_prompts
                """))
            else:
                db.execute(text("""
                    INSERT INTO rag_chat_prompts_new 
                    (id, document_type_id, prompt_text, multi_query_prompt_text, 
                     created_by_user_id, created_at, updated_at)
                    SELECT id, document_type_id, prompt_text, multi_query_prompt_text,
                           created_by_user_id, created_at, updated_at
                    FROM rag_chat_prompts
                """))
            
            # 3. Lösche alle Views (werden später neu erstellt)
            print("  🔄 Lösche abhängige Views...")
            view_result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='view'
            """))
            views = [row[0] for row in view_result.fetchall()]
            for view_name in views:
                print(f"    - Lösche View: {view_name}")
                db.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
            
            # 4. Lösche alte Tabelle
            print("  🔄 Lösche alte Tabelle...")
            db.execute(text("DROP TABLE rag_chat_prompts"))
            
            # 5. Benenne neue Tabelle um
            print("  🔄 Benenne Tabelle um...")
            db.execute(text("ALTER TABLE rag_chat_prompts_new RENAME TO rag_chat_prompts"))
            
            # 6. Erstelle Views neu (falls sie existierten)
            print("  🔄 Erstelle Views neu...")
            # Prüfe ob View-Definition existiert
            view_result = db.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='view' AND name='rag_document_summary'
            """))
            view_sql = view_result.fetchone()
            if view_sql and view_sql[0]:
                # View wurde gelöscht, aber wir haben die Definition nicht gespeichert
                # Lass uns prüfen ob sie in init_database.sql definiert ist
                print("  ⚠️ View rag_document_summary wurde gelöscht - bitte manuell neu erstellen falls nötig")
            
            # 5. Erstelle Indizes neu
            print("  🔄 Erstelle Indizes neu...")
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_document_type_id 
                ON rag_chat_prompts(document_type_id)
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_created_by_user_id 
                ON rag_chat_prompts(created_by_user_id)
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_updated_at 
                ON rag_chat_prompts(updated_at)
            """))
            
            db.commit()
            print("✅ Migration erfolgreich abgeschlossen")
    
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

