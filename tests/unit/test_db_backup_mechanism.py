"""
Unit Tests für Datenbank-Backup-Mechanismus.

TDD Phase 1: RED - Tests für automatisches DB-Backup vor Schema-Änderungen.

Gemäß PROJECT_RULES: KEIN Schema-Change ohne Backup!
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
import shutil


# ========================================
# Test 1: Backup-Mechanismus Grundfunktionalität
# ========================================

def test_db_backup_creates_backup_file():
    """
    DB-Backup sollte eine Kopie der Datenbank mit Zeitstempel erstellen.
    
    Requirements:
    - Backup-Datei wird erstellt
    - Zeitstempel im Dateinamen (YYYYMMDD_HHMMSS)
    - Original-Datei bleibt unverändert
    """
    from backend.app.db_backup import create_db_backup
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Erstelle Dummy-DB
        db_path = os.path.join(tmpdir, 'test.db')
        with open(db_path, 'w') as f:
            f.write('dummy db content')
        
        # Erstelle Backup
        backup_path = create_db_backup(db_path, backup_dir=tmpdir)
        
        # Assertions
        assert backup_path is not None, "Backup-Pfad sollte zurückgegeben werden"
        assert os.path.exists(backup_path), f"Backup-Datei sollte existieren: {backup_path}"
        assert 'test_backup_' in backup_path, "Backup sollte 'backup' im Namen haben"
        
        # Prüfe Zeitstempel-Format (YYYYMMDD_HHMMSS)
        filename = os.path.basename(backup_path)
        assert len(filename) > 20, "Filename sollte Zeitstempel enthalten"
        
        # Original sollte noch existieren
        assert os.path.exists(db_path), "Original-DB sollte noch existieren"


def test_db_backup_preserves_content():
    """
    Backup sollte exakten Inhalt der Original-DB haben.
    
    Requirements:
    - Backup ist byte-identisch mit Original
    - Keine Datenverluste
    """
    from backend.app.db_backup import create_db_backup
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Erstelle DB mit Inhalt
        db_path = os.path.join(tmpdir, 'test.db')
        original_content = b'SQLite database content with binary data \x00\x01\x02'
        with open(db_path, 'wb') as f:
            f.write(original_content)
        
        # Backup
        backup_path = create_db_backup(db_path, backup_dir=tmpdir)
        
        # Prüfe Inhalt
        with open(backup_path, 'rb') as f:
            backup_content = f.read()
        
        assert backup_content == original_content, "Backup sollte identischen Inhalt haben"


# ========================================
# Test 2: Backup vor Schema-Änderungen
# ========================================

def test_backup_before_migration_is_mandatory():
    """
    Schema-Änderungen MÜSSEN Backup erstellen.
    
    Requirements:
    - run_migration() erstellt automatisch Backup
    - Migration schlägt fehl wenn Backup nicht möglich
    """
    from backend.app.db_backup import run_migration_with_backup
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        with open(db_path, 'w') as f:
            f.write('db')
        
        # Mock Migration Function
        migration_called = []
        def mock_migration():
            migration_called.append(True)
        
        # Run mit Backup
        result = run_migration_with_backup(
            db_path=db_path,
            migration_func=mock_migration,
            backup_dir=tmpdir
        )
        
        # Assertions
        assert result['backup_created'], "Backup sollte erstellt worden sein"
        assert len(migration_called) == 1, "Migration sollte ausgeführt worden sein"
        assert os.path.exists(result['backup_path']), "Backup-Datei sollte existieren"


def test_migration_fails_if_backup_impossible():
    """
    Migration sollte fehlschlagen wenn Backup nicht erstellt werden kann.
    
    Requirements:
    - Kein Backup → Keine Migration
    - Exception wird geworfen
    - Original-DB unverändert
    """
    from backend.app.db_backup import run_migration_with_backup
    
    # DB-Pfad der nicht existiert
    result = run_migration_with_backup(
        db_path='/nonexistent/path/test.db',
        migration_func=lambda: None,
        backup_dir='/tmp'
    )
    
    # Assertions
    assert result['backup_created'] is False, "Backup sollte fehlgeschlagen sein"
    assert result['migration_executed'] is False, "Migration sollte NICHT ausgeführt worden sein"
    assert 'error' in result, "Result sollte Fehler enthalten"


# ========================================
# Test 3: Backup-Dateiname mit Zeitstempel
# ========================================

def test_backup_filename_contains_timestamp():
    """
    Backup-Dateiname MUSS Zeitstempel enthalten.
    
    Requirements:
    - Format: {basename}_backup_YYYYMMDD_HHMMSS.db
    - Keine Überschreibung vorheriger Backups
    """
    from backend.app.db_backup import generate_backup_filename
    
    db_path = 'data/qms.db'
    
    # Generiere Filename
    backup_name = generate_backup_filename(db_path)
    
    # Assertions
    assert 'qms_backup_' in backup_name, "Backup sollte 'backup' enthalten"
    assert backup_name.endswith('.db'), "Backup sollte .db Extension haben"
    
    # Prüfe Zeitstempel (Format: YYYYMMDD_HHMMSS)
    # z.B. qms_backup_20251113_143000.db
    parts = backup_name.replace('.db', '').split('_')
    assert len(parts) >= 4, "Filename sollte Datum und Zeit enthalten"


def test_backup_does_not_overwrite_existing():
    """
    Mehrfache Backups sollten nicht überschrieben werden.
    
    Requirements:
    - Jedes Backup hat eindeutigen Zeitstempel
    - Alte Backups bleiben erhalten
    """
    from backend.app.db_backup import create_db_backup
    import time
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        with open(db_path, 'w') as f:
            f.write('db')
        
        # Erstelle 2 Backups nacheinander
        backup1 = create_db_backup(db_path, backup_dir=tmpdir)
        time.sleep(1)  # 1 Sekunde warten
        backup2 = create_db_backup(db_path, backup_dir=tmpdir)
        
        # Assertions
        assert backup1 != backup2, "Backups sollten unterschiedliche Namen haben"
        assert os.path.exists(backup1), "Erstes Backup sollte noch existieren"
        assert os.path.exists(backup2), "Zweites Backup sollte existieren"

