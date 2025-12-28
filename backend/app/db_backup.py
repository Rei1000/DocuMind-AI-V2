"""
Datenbank-Backup-Mechanismus.

Gemäß PROJECT_RULES: KEIN Schema-Change ohne Backup!

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Features:
- Automatisches DB-Backup vor Migrations
- Zeitstempel im Dateinamen
- Sichere Kopie (keine Überschreibung)
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable


def generate_backup_filename(db_path: str) -> str:
    """
    Generiere Backup-Dateinamen mit Zeitstempel.
    
    Args:
        db_path: Pfad zur Original-DB
        
    Returns:
        Backup-Dateiname (ohne Pfad)
        
    Beispiel:
        data/qms.db → qms_backup_20251113_143000.db
    """
    # Hole Basename ohne Extension
    basename = Path(db_path).stem
    
    # Zeitstempel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup-Name
    backup_name = f"{basename}_backup_{timestamp}.db"
    
    return backup_name


def create_db_backup(
    db_path: str,
    backup_dir: Optional[str] = None
) -> Optional[str]:
    """
    Erstelle DB-Backup.
    
    Args:
        db_path: Pfad zur Original-DB
        backup_dir: Verzeichnis für Backup (default: gleiches wie DB)
        
    Returns:
        Pfad zum erstellten Backup oder None bei Fehler
    """
    try:
        # Prüfe ob DB existiert
        if not os.path.exists(db_path):
            print(f"⚠️ DB-Datei existiert nicht: {db_path}")
            return None
        
        # Backup-Verzeichnis
        if backup_dir is None:
            backup_dir = str(Path(db_path).parent)
        
        # Erstelle Backup-Verzeichnis falls nicht vorhanden
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Generiere Backup-Filename
        backup_name = generate_backup_filename(db_path)
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Kopiere DB
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ DB-Backup erstellt: {backup_path}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des DB-Backups: {e}")
        return None


def run_migration_with_backup(
    db_path: str,
    migration_func: Callable,
    backup_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Führe Migration mit automatischem Backup aus.
    
    WICHTIG: Backup MUSS vor Migration erfolgreich sein!
    
    Args:
        db_path: Pfad zur DB
        migration_func: Migration-Funktion die ausgeführt werden soll
        backup_dir: Backup-Verzeichnis
        
    Returns:
        Dict mit Result-Informationen
    """
    result = {
        'backup_created': False,
        'backup_path': None,
        'migration_executed': False,
        'error': None
    }
    
    try:
        # 1. Erstelle Backup
        backup_path = create_db_backup(db_path, backup_dir)
        
        if not backup_path:
            result['error'] = 'Backup konnte nicht erstellt werden'
            print("❌ Migration abgebrochen: Kein Backup möglich")
            return result
        
        result['backup_created'] = True
        result['backup_path'] = backup_path
        
        # 2. Führe Migration aus
        print(f"🔄 Führe Migration aus (Backup: {backup_path})")
        migration_func()
        
        result['migration_executed'] = True
        print("✅ Migration erfolgreich abgeschlossen")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Fehler bei Migration: {e}")
    
    return result

