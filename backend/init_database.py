#!/usr/bin/env python3
"""
DocuMind-AI V2 - Datenbank-Initialisierungs-Script

Dieses Script erstellt die komplette Datenbank von Grund auf.
Es ersetzt alle Migration-Scripts und ist die Single Source of Truth.

Verwendung:
    python3 init_database.py [--force]

Optionen:
    --force    Überschreibt die bestehende Datenbank ohne Bestätigung

Autor: AI Assistant
Version: 2.5.1
Stand: 2025-11-11
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

# Konfiguration
DATABASE_PATH = "/Users/reiner/Documents/DocuMind-AI-V2/data/qms.db"
SQL_SCRIPT_PATH = "/Users/reiner/Documents/DocuMind-AI-V2/backend/init_database.sql"
BACKUP_DIR = "/Users/reiner/Documents/DocuMind-AI-V2/data"

def create_backup():
    """Erstellt ein Backup der bestehenden Datenbank."""
    if os.path.exists(DATABASE_PATH):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{BACKUP_DIR}/qms_backup_init_{timestamp}.db"
        
        print(f"📦 Erstelle Backup: {backup_path}")
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✅ Backup erfolgreich erstellt: {backup_path}")
        return backup_path
    return None

def confirm_overwrite():
    """Fragt den Benutzer, ob die Datenbank überschrieben werden soll."""
    print(f"⚠️  ACHTUNG: Die bestehende Datenbank wird überschrieben!")
    print(f"   Pfad: {DATABASE_PATH}")
    print(f"   Ein Backup wird automatisch erstellt.")
    print()
    
    while True:
        response = input("Möchten Sie fortfahren? (ja/nein): ").lower().strip()
        if response in ['ja', 'j', 'yes', 'y']:
            return True
        elif response in ['nein', 'n', 'no']:
            return False
        else:
            print("Bitte antworten Sie mit 'ja' oder 'nein'.")

def init_database(force=False):
    """Initialisiert die Datenbank."""
    
    # Prüfe ob SQL-Script existiert
    if not os.path.exists(SQL_SCRIPT_PATH):
        print(f"❌ SQL-Script nicht gefunden: {SQL_SCRIPT_PATH}")
        return False
    
    # Prüfe ob Datenbank bereits existiert
    if os.path.exists(DATABASE_PATH):
        if not force:
            if not confirm_overwrite():
                print("❌ Initialisierung abgebrochen.")
                return False
        
        # Erstelle Backup
        backup_path = create_backup()
        if backup_path:
            print(f"🗑️  Lösche alte Datenbank...")
            os.remove(DATABASE_PATH)
    
    # Erstelle data/ Verzeichnis falls es nicht existiert
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    print(f"🚀 Initialisiere Datenbank: {DATABASE_PATH}")
    
    try:
        # Verbinde zur SQLite-Datenbank
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Lese SQL-Script
        print(f"📖 Lese SQL-Script: {SQL_SCRIPT_PATH}")
        with open(SQL_SCRIPT_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Führe SQL-Script aus
        print("⚙️  Führe SQL-Script aus...")
        cursor.executescript(sql_script)
        
        # Committe Änderungen
        conn.commit()
        
        # Prüfe Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"✅ Datenbank erfolgreich initialisiert!")
        print(f"📊 Erstellte Tabellen: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Prüfe Seed-Daten
        cursor.execute("SELECT COUNT(*) FROM interest_groups")
        interest_groups_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM document_types")
        document_types_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_qms_admin = 1")
        admin_users_count = cursor.fetchone()[0]
        
        print(f"🌱 Seed-Daten:")
        print(f"   - Interest Groups: {interest_groups_count}")
        print(f"   - Document Types: {document_types_count}")
        print(f"   - QMS Admin Users: {admin_users_count}")
        
        # Prüfe Indizes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        print(f"🔍 Erstellte Indizes: {len(indexes)}")
        
        # Prüfe Views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print(f"👁️  Erstellte Views: {len(views)}")
        
        conn.close()
        
        print()
        print("🎉 Datenbank-Initialisierung erfolgreich abgeschlossen!")
        print(f"📁 Datenbank-Pfad: {DATABASE_PATH}")
        print(f"🔑 QMS Admin Login: qms.admin@company.com / Admin432!")
        print()
        print("Nächste Schritte:")
        print("1. Starte das System: ./start.sh local")
        print("2. Logge dich als QMS Admin ein")
        print("3. Teste die Funktionen")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Initialisierung: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description="DocuMind-AI V2 - Datenbank-Initialisierung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    python3 init_database.py              # Interaktive Initialisierung
    python3 init_database.py --force      # Überschreibt ohne Bestätigung
        """
    )
    
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='Überschreibt die bestehende Datenbank ohne Bestätigung'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🗄️  DocuMind-AI V2 - Datenbank-Initialisierung")
    print("=" * 60)
    print(f"Version: 2.5.1")
    print(f"Stand: 2025-11-11")
    print(f"Datenbank: {DATABASE_PATH}")
    print(f"SQL-Script: {SQL_SCRIPT_PATH}")
    print("=" * 60)
    print()
    
    success = init_database(force=args.force)
    
    if success:
        print("✅ Initialisierung erfolgreich!")
        sys.exit(0)
    else:
        print("❌ Initialisierung fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    main()
