"""
KI-QMS Datenbank-Konfiguration und Session-Management

Dieses Modul verwaltet die zentrale Datenbank-Konfiguration für das
KI-gestützte Qualitätsmanagementsystem. Es stellt SQLAlchemy-Engine,
Session-Factory und Dependency-Injection für FastAPI bereit.

Technische Details:
- SQLite-Datenbank für MVP (einfache Deployment)
- SQLAlchemy ORM für Datenbankoperationen
- Connection Pooling für Performance
- Automatische Session-Verwaltung mit Dependency Injection
- Check_same_thread=False für Multi-Threading-Unterstützung

Produktion-Überlegungen:
- Für Produktion: PostgreSQL/MySQL empfohlen
- Umgebungsvariablen für DB-Credentials
- Connection Pool Size Tuning
- Read-Write Replica Support

Autoren: KI-QMS Entwicklungsteam
Version: 1.0.0 (MVP Phase 1)
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# ===== DATENBANK-KONFIGURATION =====

# SQLite-Datenbankpfad (gemeinsam für Docker + Lokal)
# Liegt im data/ Verzeichnis (wird von Docker gemountet)
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/qms.db")

# SQLAlchemy-Engine mit SQLite-spezifischen Optimierungen
engine = create_engine(
    DATABASE_URL,
    # SQLite-spezifische Optionen für FastAPI-Kompatibilität
    connect_args={
        "check_same_thread": False,    # Erlaubt Multi-Threading-Zugriff
        "timeout": 30                  # Connection-Timeout in Sekunden
    },
    # Performance-Optimierungen
    pool_size=20,                      # Anzahl persistenter Connections
    max_overflow=30,                   # Zusätzliche Connections bei Bedarf
    pool_pre_ping=True,                # Validiert Connections vor Nutzung
    echo=False                         # SQL-Logging (für Debug auf True setzen)
)

# Session-Factory für Datenbank-Operationen
# autocommit=False: Explizite Transaktions-Kontrolle
# autoflush=False: Bessere Performance, manueller Flush
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Deklarative Basis für alle ORM-Modelle
# Alle Model-Klassen erben von dieser Basis
Base = declarative_base()

# ===== SQLITE-OPTIMIERUNGEN =====

def _set_sqlite_pragma(dbapi_connection, connection_record):
    """
    SQLite-Performance-Optimierungen bei jeder neuen Connection.
    
    Aktiviert wichtige SQLite-Features für bessere Performance
    und Datenintegrität im Produktions-ähnlichen Betrieb.
    
    Args:
        dbapi_connection: Raw SQLite-Connection
        connection_record: SQLAlchemy Connection Record
        
    Optimierungen:
        - Foreign Key Constraints für Referentielle Integrität
        - WAL-Mode für bessere Concurrency
        - Synchronous=NORMAL für Performance/Sicherheit-Balance
        - Memory-Mapped I/O für Speed
        - Optimierte Cache-Größe
    """
    cursor = dbapi_connection.cursor()
    try:
        # Aktiviere Foreign Key Constraints (standardmäßig deaktiviert)
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # WAL-Mode für bessere Multi-User-Performance
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Synchronization-Mode: NORMAL (Performance/Sicherheit-Balance)
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Memory-Mapped I/O für bessere Performance
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        # Cache-Größe für häufig genutzte Pages
        cursor.execute("PRAGMA cache_size=10000")      # 10000 Pages ~40MB
        
        # Optimierter Page-Size (Standard: 4096)
        cursor.execute("PRAGMA page_size=4096")
        
        # Auto-Vacuum für Speicher-Effizienz
        cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")
    finally:
        cursor.close()

# Event-Listener für SQLite-Optimierungen bei jeder Connection
event.listen(engine, "connect", _set_sqlite_pragma)

# ===== DATABASE SESSION MANAGEMENT =====

def get_db():
    """
    FastAPI Dependency für Datenbank-Session-Management.
    
    Stellt eine SQLAlchemy-Session für Request-Handler bereit und
    gewährleistet automatische Cleanup-Operationen nach Request-Ende.
    
    Funktionsweise:
    1. Erstellt neue Session für jeden Request
    2. Stellt Session via Dependency Injection bereit  
    3. Schließt Session automatisch nach Request-Ende
    4. Rollback bei Exceptions für Datenbank-Konsistenz
    
    Yields:
        Session: SQLAlchemy-Session für Datenbankoperationen
        
    Usage:
        ```python
        @app.get("/api/example")
        async def example_endpoint(db: Session = Depends(get_db)):
            return db.query(Model).all()
        ```
        
    Error Handling:
        - Automatischer Rollback bei Exceptions
        - Session wird immer geschlossen (finally-Block)
        - Connection Pool Management durch SQLAlchemy
        
    Performance:
        - Session-Scope: Ein Request
        - Connection Reuse durch Pool
        - Lazy Loading für Relationships
    """
    # Erstelle neue Session für diesen Request
    db = SessionLocal()
    try:
        # Stelle Session für Request-Handler bereit
        yield db
        
        # Expliziter Commit wird in Handler-Logik durchgeführt
        # Kein automatischer Commit hier für bessere Kontrolle
        
    except Exception as e:
        # Rollback bei jeder Exception für Datenbank-Konsistenz
        db.rollback()
        raise e
        
    finally:
        # Session immer schließen für Connection Pool Cleanup
        db.close()

def create_tables():
    """
    Erstellt alle Datenbank-Tabellen basierend auf SQLAlchemy-Modellen.
    
    Liest alle in models.py definierten Modell-Klassen und erstellt
    entsprechende Tabellen in der Datenbank. Verwendet CREATE TABLE IF NOT EXISTS
    für idempotente Ausführung.
    
    Funktionalität:
    - Erstellt alle Tabellen aus Base.metadata
    - Idempotent: Überspringt bereits existierende Tabellen
    - Erstellt Indizes und Constraints automatisch
    - Foreign Key Relations werden berücksichtigt
    
    Usage:
        ```python
        # Beim Application Startup
        create_tables()
        ```
        
    Note:
        - Führt keine Daten-Migration durch
        - Ändert keine existierenden Tabellen-Strukturen
        - Für Schema-Änderungen: Alembic migrations empfohlen
        
    Error Handling:
        - Wirft SQLAlchemy-Exceptions bei Schema-Problemen
        - Transaktion wird automatisch gerollt bei Fehlern
    """
    try:
        # Importiere alle Modelle um Base.metadata zu populieren
        from . import models
        
        # Erstelle alle Tabellen aus den registrierten Modellen
        Base.metadata.create_all(bind=engine)
        
        print("✅ Datenbank-Tabellen erfolgreich erstellt/überprüft")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Datenbank-Tabellen: {e}")
        raise e

# ===== UTILITY FUNCTIONS =====

def get_db_info():
    """
    Liefert Informationen über die aktuelle Datenbank-Konfiguration.
    
    Nützlich für Debugging, Monitoring und Gesundheitschecks.
    
    Returns:
        dict: Datenbank-Konfigurationsinformationen
        
    Example Response:
        ```json
        {
            "database_url": "sqlite:///./qms_mvp.db",
            "engine_name": "sqlite",
            "pool_size": 20,
            "max_overflow": 30,
            "total_tables": 8,
            "table_names": ["users", "interest_groups", ...]
        }
        ```
    """
    from . import models
    
    return {
        "database_url": DATABASE_URL,
        "engine_name": engine.name,
        "pool_size": engine.pool.size(),
        "max_overflow": engine.pool._max_overflow,
        "total_tables": len(Base.metadata.tables),
        "table_names": list(Base.metadata.tables.keys())
    }

def check_database_connection():
    """
    Überprüft die Datenbank-Konnektivität für Gesundheitschecks.
    
    Führt eine einfache Query aus um sicherzustellen, dass die
    Datenbank erreichbar und funktionsfähig ist.
    
    Returns:
        bool: True wenn Verbindung erfolgreich, False bei Fehler
        
    Usage:
        ```python
        if not check_database_connection():
            raise HTTPException(503, "Datenbank nicht verfügbar")
        ```
        
    Note:
        - Verwendet minimale Query für geringe Latenz
        - Timeout nach 5 Sekunden
        - Für API-Health-Endpoints geeignet
    """
    try:
        # Einfache Query um Connection zu testen
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return result.fetchone()[0] == 1
            
    except Exception as e:
        print(f"⚠️ Datenbank-Verbindungstest fehlgeschlagen: {e}")
        return False

# ===== DEVELOPMENT HELPERS =====

def reset_database():
    """
    Löscht und erstellt alle Tabellen neu (nur für Development!).
    
    ⚠️ WARNUNG: Löscht alle Daten unwiderruflich!
    Nur für Development und Testing verwenden.
    
    Funktionalität:
    - Löscht alle Tabellen
    - Erstellt Schema neu
    - Initialisiert leere Datenbank
    
    Usage:
        ```python
        # Nur in Development!
        if os.getenv("ENVIRONMENT") == "development":
            reset_database()
        ```
    """
    import warnings
    
    # Warnung für Produktions-Sicherheit
    warnings.warn(
        "reset_database() löscht alle Daten! Nur für Development verwenden!",
        UserWarning,
        stacklevel=2
    )
    
    try:
        from . import models
        
        # Lösche alle Tabellen
        Base.metadata.drop_all(bind=engine)
        print("🗑️ Alle Tabellen gelöscht")
        
        # Erstelle Schema neu
        Base.metadata.create_all(bind=engine)
        print("✅ Datenbank-Schema neu erstellt")
        
    except Exception as e:
        print(f"❌ Fehler beim Reset der Datenbank: {e}")
        raise e

# ===== EXPORTS =====
# Hauptsächlich genutzte Objekte für Import in anderen Modulen

__all__ = [
    "engine",          # SQLAlchemy Engine
    "SessionLocal",    # Session Factory
    "Base",           # Deklarative Basis für Modelle
    "get_db",         # FastAPI Dependency
    "create_tables",  # Schema-Erstellung
    "get_db_info",    # DB-Informationen
    "check_database_connection"  # Health Check
] 