"""
Application Service für Interest Groups
Orchestriert Domain Entities und Repository
Gibt Legacy-kompatible Responses zurück
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.schemas import InterestGroupCreate, InterestGroupUpdate, InterestGroup
from contexts.interestgroups.domain import InterestGroup as InterestGroupEntity
from contexts.interestgroups.infrastructure.repositories import InterestGroupRepositoryImpl
from contexts.interestgroups.infrastructure.mappers import InterestGroupMapper


class InterestGroupService:
    """
    Application Service für Interest Groups
    Arbeitet mit Domain Entities intern, gibt Legacy Schemas nach außen
    """
    
    def __init__(self):
        """Service ohne direkte Repository-Abhängigkeit (wird per Method Injection übergeben)"""
        pass
    
    def list_groups(self, db: Session) -> List[InterestGroup]:
        """
        Liste aller aktiven Interest Groups
        
        Returns:
            Liste von InterestGroup Schemas (Legacy-kompatibel)
        """
        repository = InterestGroupRepositoryImpl(db)
        entities = repository.find_all_active()
        
        # Konvertiere zu Schema-kompatiblen Dicts
        result = []
        for entity in entities:
            schema_dict = InterestGroupMapper.to_schema_dict(entity)
            result.append(InterestGroup(**schema_dict))
        
        return result
    
    def get_group(self, db: Session, group_id: int) -> Optional[InterestGroup]:
        """
        Hole einzelne Interest Group nach ID
        
        Returns:
            InterestGroup Schema oder None
        """
        repository = InterestGroupRepositoryImpl(db)
        entity = repository.find_by_id(group_id)
        
        if not entity:
            return None
            
        schema_dict = InterestGroupMapper.to_schema_dict(entity)
        return InterestGroup(**schema_dict)
    
    def get_group_by_code(self, db: Session, code: str) -> Optional[InterestGroup]:
        """
        Hole Interest Group nach Code (für Duplicate-Check)
        
        Returns:
            InterestGroup Schema oder None
        """
        repository = InterestGroupRepositoryImpl(db)
        entity = repository.find_by_code(code)
        
        if not entity:
            return None
            
        schema_dict = InterestGroupMapper.to_schema_dict(entity)
        return InterestGroup(**schema_dict)
    
    def create_group(self, db: Session, group_data: InterestGroupCreate) -> InterestGroup:
        """
        Erstelle neue Interest Group
        
        Args:
            db: Database Session
            group_data: Creation Data
            
        Returns:
            Erstellte InterestGroup (Schema)
        """
        repository = InterestGroupRepositoryImpl(db)
        
        # Defensive Defaults für optionale Felder
        if group_data.group_permissions is None or group_data.group_permissions == "":
            group_data.group_permissions = []
        
        # 1. Vor dem Insert: Duplicate-Check für Legacy-Compat
        if group_data.code:
            existing = repository.find_by_code(group_data.code)
            if existing:
                # Legacy-Verhalten: Bei Duplikat existierenden Eintrag zurückgeben
                schema_dict = InterestGroupMapper.to_schema_dict(existing)
                return InterestGroup(**schema_dict)
        
        # 2. Erstelle Domain Entity
        try:
            entity = InterestGroupEntity.create(
                name=group_data.name,
                code=group_data.code,
                description=group_data.description,
                permissions=group_data.group_permissions,
                ai_functionality=group_data.ai_functionality,
                typical_tasks=group_data.typical_tasks,
                is_external=group_data.is_external if hasattr(group_data, 'is_external') else False
            )
            
            # 3. Speichere Entity
            saved_entity = repository.save(entity)
            
            # 4. Process Domain Events (könnte für Event-Bus verwendet werden)
            events = saved_entity.pull_domain_events()
            # TODO: Event-Handler aufrufen wenn implementiert
            
            # 5. Konvertiere zu Schema
            schema_dict = InterestGroupMapper.to_schema_dict(saved_entity)
            return InterestGroup(**schema_dict)
            
        except ValueError as e:
            # Bei Constraint-Violations versuche existierenden Eintrag zu finden
            if "already exists" in str(e) and group_data.code:
                existing = repository.find_by_code(group_data.code)
                if existing:
                    schema_dict = InterestGroupMapper.to_schema_dict(existing)
                    return InterestGroup(**schema_dict)
            raise
    
    def update_group(self, db: Session, group_id: int, group_data: InterestGroupUpdate) -> Optional[InterestGroup]:
        """
        Update Interest Group
        
        Returns:
            Aktualisierte InterestGroup oder None
        """
        repository = InterestGroupRepositoryImpl(db)
        
        # 1. Lade existierende Entity
        entity = repository.find_by_id(group_id)
        if not entity:
            return None
        
        # 2. Update nur gesetzte Felder
        update_dict = group_data.dict(exclude_unset=True)
        
        # 3. Führe Domain Update aus
        entity.update(
            name=update_dict.get('name'),
            description=update_dict.get('description'),
            permissions=update_dict.get('group_permissions'),
            ai_functionality=update_dict.get('ai_functionality'),
            typical_tasks=update_dict.get('typical_tasks'),
            is_external=update_dict.get('is_external')
        )
        
        # 4. Speichere Änderungen
        saved_entity = repository.save(entity)
        
        # 5. Process Domain Events
        events = saved_entity.pull_domain_events()
        # TODO: Event-Handler aufrufen wenn implementiert
        
        # 6. Konvertiere zu Schema
        schema_dict = InterestGroupMapper.to_schema_dict(saved_entity)
        return InterestGroup(**schema_dict)
    
    def delete_group(self, db: Session, group_id: int) -> bool:
        """
        Soft-Delete Interest Group
        
        Returns:
            True wenn erfolgreich, False wenn nicht gefunden
        """
        repository = InterestGroupRepositoryImpl(db)
        
        # 1. Lade Entity
        entity = repository.find_by_id(group_id)
        if not entity:
            return False
        
        # 2. Deaktiviere (Soft Delete)
        entity.deactivate()
        
        # 3. Speichere
        repository.save(entity)
        
        # 4. Process Domain Events
        events = entity.pull_domain_events()
        # TODO: Event-Handler aufrufen wenn implementiert
        
        return True


# Legacy Service bleibt für Fallback verfügbar
class InterestGroupServiceLegacy:
    """
    Legacy Service - verwendet direkt SQLAlchemy Models
    NICHT ÄNDERN - nur für Rückwärtskompatibilität
    """
    
    def __init__(self, repository):
        """Initialisiere Service mit Repository (Dependency Injection)"""
        self.repository = repository
    
    def list_groups(self, db: Session) -> List[InterestGroup]:
        """Liste aller aktiven Interest Groups"""
        return self.repository.list(db)
    
    def get_group(self, db: Session, group_id: int) -> Optional[InterestGroup]:
        """Hole einzelne Interest Group nach ID"""
        return self.repository.get(db, group_id)
    
    def get_group_by_code(self, db: Session, code: str) -> Optional[InterestGroup]:
        """Hole Interest Group nach Code (für Duplicate-Check)"""
        return self.repository.get_by_code(db, code)
    
    def create_group(self, db: Session, group_data: InterestGroupCreate) -> InterestGroup:
        """Erstelle neue Interest Group mit Legacy-Repository"""
        
        # Defensive Defaults für optionale Felder
        if group_data.group_permissions is None or group_data.group_permissions == "":
            group_data.group_permissions = []
        
        # Legacy-Verhalten bei Duplikaten
        if group_data.code:
            try:
                existing_group = self.repository.get_by_code(db, group_data.code)
                if existing_group:
                    return existing_group
            except Exception:
                pass
        
        try:
            return self.repository.create(db, group_data)
        except IntegrityError as e:
            db.rollback()
            
            if group_data.code:
                try:
                    existing_group = self.repository.get_by_code(db, group_data.code)
                    if existing_group:
                        return existing_group
                except Exception:
                    pass
            
            raise ValueError(f"Duplicate constraint violation: {str(e)}")
        except Exception as e:
            db.rollback()
            raise e
    
    def update_group(self, db: Session, group_id: int, group_data: InterestGroupUpdate) -> Optional[InterestGroup]:
        """Update Interest Group"""
        return self.repository.update(db, group_id, group_data)
    
    def delete_group(self, db: Session, group_id: int) -> bool:
        """Soft-Delete Interest Group"""
        return self.repository.delete(db, group_id)