"""
Infrastructure Repositories für Access Control
"""

import sqlite3
from typing import Optional
from contexts.accesscontrol.domain.entities import User
from contexts.accesscontrol.domain.repositories import UserRepository


class UserRepositoryImpl(UserRepository):
    """SQLite-Implementierung des User-Repositories"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            # Verwende DATABASE_URL aus der Umgebung (Single Source of Truth)
            database_url = os.getenv("DATABASE_URL", "sqlite:///qms_mvp.db")
            if database_url.startswith("sqlite:///"):
                db_path = database_url.replace("sqlite:///", "")
            else:
                db_path = database_url
        self.db_path = db_path
        print(f"[REPO] UserRepositoryImpl initialized with db_path={self.db_path}")
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Findet einen User anhand der E-Mail-Adresse"""
        try:
            # Log für DB-Binding-Diagnose
            import os
            print(f"[DB-BIND] endpoint=login engine_url=sqlite:///{self.db_path} db_env=DATABASE_URL={os.getenv('DATABASE_URL')} SQLALCHEMY_DATABASE_URL={os.getenv('SQLALCHEMY_DATABASE_URL')}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, email, full_name, hashed_password, is_active FROM users WHERE email = ?",
                    (email,)
                )
                row = cursor.fetchone()
                
                if row:
                    user_id, email, full_name, hashed_password, is_active = row
                    return User(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        hashed_password=hashed_password,
                        is_active=bool(is_active)
                    )
                return None
        except Exception as e:
            print(f"[REPO] find_by_email error: {e}")
            return None
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Findet einen User anhand der ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, email, full_name, hashed_password, is_active FROM users WHERE id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    user_id, email, full_name, hashed_password, is_active = row
                    return User(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        hashed_password=hashed_password,
                        is_active=bool(is_active)
                    )
                return None
        except Exception as e:
            print(f"[REPO] find_by_id error: {e}")
            return None
    
    def save(self, user: User) -> User:
        """Speichert einen User"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if user.id is None:
                    # Neuer User
                    cursor.execute(
                        "INSERT INTO users (email, full_name, hashed_password, is_active) VALUES (?, ?, ?, ?)",
                        (user.email, user.full_name, user.hashed_password, user.is_active)
                    )
                    user.id = cursor.lastrowid
                else:
                    # Update bestehender User
                    cursor.execute(
                        "UPDATE users SET email = ?, full_name = ?, hashed_password = ?, is_active = ? WHERE id = ?",
                        (user.email, user.full_name, user.hashed_password, user.is_active, user.id)
                    )
                
                conn.commit()
                return user
        except Exception as e:
            print(f"[REPO] save error: {e}")
            raise
