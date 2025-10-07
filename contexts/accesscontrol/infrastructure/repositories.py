"""
Infrastructure Repositories für Access Control
"""

from typing import Optional
from sqlalchemy.orm import Session
from contexts.accesscontrol.domain.entities import User as DomainUser
from contexts.accesscontrol.domain.repositories import UserRepository
from backend.app.models import User as SQLAlchemyUser


class UserRepositoryImpl(UserRepository):
    """SQLAlchemy-Implementierung des User-Repositories"""
    
    def __init__(self, db: Session):
        """
        Initialize repository with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        print(f"[REPO] UserRepositoryImpl initialized with SQLAlchemy session")
    
    def find_by_email(self, email: str) -> Optional[DomainUser]:
        """Findet einen User anhand der E-Mail-Adresse"""
        try:
            # Query SQLAlchemy User model
            user = self.db.query(SQLAlchemyUser).filter(SQLAlchemyUser.email == email).first()
            
            if user:
                # Map SQLAlchemy model to Domain entity
                return DomainUser(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name or "",
                    hashed_password=user.hashed_password,
                    is_active=user.is_active
                )
            return None
        except Exception as e:
            print(f"[REPO] find_by_email error: {e}")
            return None
    
    def find_by_id(self, user_id: int) -> Optional[DomainUser]:
        """Findet einen User anhand der ID"""
        try:
            # Query SQLAlchemy User model
            user = self.db.query(SQLAlchemyUser).filter(SQLAlchemyUser.id == user_id).first()
            
            if user:
                # Map SQLAlchemy model to Domain entity
                return DomainUser(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name or "",
                    hashed_password=user.hashed_password,
                    is_active=user.is_active
                )
            return None
        except Exception as e:
            print(f"[REPO] find_by_id error: {e}")
            return None
    
    def save(self, user: DomainUser) -> DomainUser:
        """Speichert einen User"""
        try:
            if user.id is None:
                # Neuer User - Create SQLAlchemy model
                db_user = SQLAlchemyUser(
                    email=user.email,
                    full_name=user.full_name,
                    hashed_password=user.hashed_password,
                    is_active=user.is_active
                )
                self.db.add(db_user)
                self.db.commit()
                self.db.refresh(db_user)
                user.id = db_user.id
            else:
                # Update bestehender User
                db_user = self.db.query(SQLAlchemyUser).filter(SQLAlchemyUser.id == user.id).first()
                if db_user:
                    db_user.email = user.email
                    db_user.full_name = user.full_name
                    db_user.hashed_password = user.hashed_password
                    db_user.is_active = user.is_active
                    self.db.commit()
            
            return user
        except Exception as e:
            self.db.rollback()
            print(f"[REPO] save error: {e}")
            raise
