"""
Repository Implementierung für Interest Groups
Nutzt SQLAlchemy Models aber arbeitet mit Domain Entities
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from backend.app.models import InterestGroup as InterestGroupModel
from backend.app.schemas import InterestGroupCreate, InterestGroupUpdate

from contexts.interestgroups.domain import (
    InterestGroup as InterestGroupEntity,
    InterestGroupRepository
)
from .mappers import InterestGroupMapper


class InterestGroupRepositoryImpl(InterestGroupRepository):
    """
    Konkrete Repository Implementierung
    Implementiert das Domain Repository Interface
    Nutzt Legacy SQLAlchemy Models intern
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def find_by_id(self, group_id: int) -> Optional[InterestGroupEntity]:
        """Findet Interest Group nach ID"""
        model = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.id == group_id
        ).first()
        
        return InterestGroupMapper.to_domain(model) if model else None
    
    def find_by_code(self, code: str) -> Optional[InterestGroupEntity]:
        """Findet Interest Group nach Code"""
        model = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.code == code,
            InterestGroupModel.is_active == True
        ).first()
        
        return InterestGroupMapper.to_domain(model) if model else None
    
    def find_by_name(self, name: str) -> Optional[InterestGroupEntity]:
        """Findet Interest Group nach Name"""
        model = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.name == name,
            InterestGroupModel.is_active == True
        ).first()
        
        return InterestGroupMapper.to_domain(model) if model else None
    
    def find_all_active(self) -> List[InterestGroupEntity]:
        """Gibt alle aktiven Interest Groups zurück"""
        models = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.is_active == True
        ).all()
        
        return [InterestGroupMapper.to_domain(model) for model in models]
    
    def find_all(self) -> List[InterestGroupEntity]:
        """Gibt alle Interest Groups zurück"""
        models = self.db.query(InterestGroupModel).all()
        return [InterestGroupMapper.to_domain(model) for model in models]
    
    def save(self, interest_group: InterestGroupEntity) -> InterestGroupEntity:
        """
        Speichert Interest Group (create oder update)
        """
        if interest_group.id:
            # Update existierende Group
            existing_model = self.db.query(InterestGroupModel).filter(
                InterestGroupModel.id == interest_group.id
            ).first()
            
            if not existing_model:
                raise ValueError(f"Interest Group with id {interest_group.id} not found")
                
            model = InterestGroupMapper.to_model(interest_group, existing_model)
        else:
            # Neue Group erstellen
            model = InterestGroupMapper.to_model(interest_group)
            self.db.add(model)
        
        try:
            self.db.commit()
            self.db.refresh(model)
            
            # Konvertiere zurück zu Domain Entity mit generierter ID
            saved_entity = InterestGroupMapper.to_domain(model)
            
            # Übertrage Domain Events
            saved_entity._events = interest_group._events
            
            return saved_entity
            
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                if "interest_groups.code" in str(e):
                    raise ValueError(f"Interest group with code '{interest_group.code}' already exists")
                elif "interest_groups.name" in str(e):
                    raise ValueError(f"Interest group with name '{interest_group.name}' already exists")
            raise
    
    def exists_with_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """Prüft ob Code bereits existiert"""
        query = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.code == code,
            InterestGroupModel.is_active == True
        )
        
        if exclude_id:
            query = query.filter(InterestGroupModel.id != exclude_id)
            
        return query.first() is not None
    
    def exists_with_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Prüft ob Name bereits existiert"""
        query = self.db.query(InterestGroupModel).filter(
            InterestGroupModel.name == name,
            InterestGroupModel.is_active == True
        )
        
        if exclude_id:
            query = query.filter(InterestGroupModel.id != exclude_id)
            
        return query.first() is not None
    
    def count_active(self) -> int:
        """Zählt aktive Interest Groups"""
        return self.db.query(InterestGroupModel).filter(
            InterestGroupModel.is_active == True
        ).count()
    
    def find_by_permission(self, permission: str) -> List[InterestGroupEntity]:
        """Findet Groups mit bestimmter Permission"""
        # Da Permissions als JSON gespeichert sind, müssen wir filtern
        all_active = self.find_all_active()
        
        result = []
        for group in all_active:
            if group.has_permission(permission):
                result.append(group)
                
        return result


class InterestGroupRepositoryLegacy:
    """
    Legacy Repository für Rückwärtskompatibilität
    Arbeitet direkt mit Schemas (nicht mit Domain Entities)
    DIESE KLASSE BLEIBT UNVERÄNDERT für Legacy-Kompatibilität
    """
    
    def list(self, db: Session) -> List[InterestGroupModel]:
        """Liste aller aktiven Interest Groups (wie im bestehenden Code)"""
        return db.query(InterestGroupModel).filter(
            InterestGroupModel.is_active == True
        ).all()
    
    def get(self, db: Session, group_id: int) -> Optional[InterestGroupModel]:
        """Hole Interest Group nach ID (wie im bestehenden Code)"""
        return db.query(InterestGroupModel).filter(
            InterestGroupModel.id == group_id
        ).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[InterestGroupModel]:
        """Hole Interest Group nach Code für Duplicate-Check"""
        return db.query(InterestGroupModel).filter(
            InterestGroupModel.code == code,
            InterestGroupModel.is_active == True
        ).first()
    
    def create(self, db: Session, group_data: InterestGroupCreate) -> InterestGroupModel:
        """Erstelle neue Interest Group (wie im bestehenden Code)"""
        # Prüfe Duplikate (wie im bestehenden Code)
        existing_name = db.query(InterestGroupModel).filter(
            InterestGroupModel.name == group_data.name,
            InterestGroupModel.is_active == True
        ).first()
        if existing_name:
            raise ValueError(f"Interest group with name '{group_data.name}' already exists")
        
        existing_code = db.query(InterestGroupModel).filter(
            InterestGroupModel.code == group_data.code,
            InterestGroupModel.is_active == True
        ).first()
        if existing_code:
            raise ValueError(f"Interest group with code '{group_data.code}' already exists")
        
        # Serialisiere group_permissions zu JSON-String vor DB-Insert
        permissions_value = group_data.group_permissions
        if isinstance(permissions_value, (list, dict)):
            permissions_value = json.dumps(permissions_value, ensure_ascii=False)
        
        # Erstelle neue Gruppe (wie im bestehenden Code)
        db_group = InterestGroupModel(
            name=group_data.name,
            code=group_data.code,
            description=group_data.description,
            group_permissions=permissions_value,
            ai_functionality=group_data.ai_functionality,
            typical_tasks=group_data.typical_tasks,
            is_external=group_data.is_external,
            is_active=group_data.is_active
        )
        
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
    
    def update(self, db: Session, group_id: int, group_data: InterestGroupUpdate) -> Optional[InterestGroupModel]:
        """Update Interest Group (wie im bestehenden Code)"""
        db_group = self.get(db, group_id)
        if not db_group:
            return None
        
        # Update nur gesetzte Felder (wie im bestehenden Code)
        update_data = group_data.dict(exclude_unset=True)
        
        # Serialisiere group_permissions wenn vorhanden
        if 'group_permissions' in update_data and update_data['group_permissions'] is not None:
            permissions_value = update_data['group_permissions']
            if isinstance(permissions_value, (list, dict)):
                update_data['group_permissions'] = json.dumps(permissions_value, ensure_ascii=False)
        
        for field, value in update_data.items():
            setattr(db_group, field, value)
        
        db.commit()
        db.refresh(db_group)
        return db_group
    
    def delete(self, db: Session, group_id: int) -> bool:
        """Soft-Delete Interest Group (wie im bestehenden Code)"""
        db_group = self.get(db, group_id)
        if not db_group:
            return False
        
        # Soft Delete
        db_group.is_active = False
        db.commit()
        return True