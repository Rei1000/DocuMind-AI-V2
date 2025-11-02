# 🔍 AccessControl Context - Analyse & Bestandsaufnahme

> **Zweck:** Analyse des bestehenden `accesscontrol` Context für RBAC-Implementierung  
> **Stand:** 2025-01-XX

---

## ✅ Was bereits vorhanden ist

### **Domain Layer** (Vollständig DDD-konform)

#### **Entities** (`domain/entities.py`)
- ✅ `User` - User Entity mit `approval_level` (aber: wird nicht aus DB gemappt!)
- ✅ `Role` - Rollen-Definition
- ✅ `Permission` - Berechtigungs-Definition
- ✅ `Assignment` - User-Role-Zuordnung
- ✅ `Membership` - User-Group-Zuordnung (mit `approval_level`)
- ✅ `ApprovalRule` - Freigabe-Regel (Placeholder)

#### **Value Objects** (`domain/value_objects.py`)
- ✅ `UserId` - User ID Value Object
- ✅ `PermissionCode` - Permission Code Value Object
- ✅ `RoleName` - Role Name Value Object
- ✅ `Email` - Email Value Object
- ✅ `ApprovalLevel` - Approval Level Value Object (1-5)

#### **Policies** (`domain/policies.py`)
- ✅ `RBACPolicy` - Kern-Business-Rules
  - `has_permission()` - Permission-Prüfung
  - `can_approve()` - Freigabe-Prüfung
  - `can_manage_users()` - User-Management-Prüfung
  - `can_access_resource()` - Resource-Zugriff-Prüfung
- ✅ `ApprovalPolicy` - Dokument-Freigabe-Regeln
- ✅ `MembershipPolicy` - Group-Membership-Regeln

#### **Repository Interfaces** (`domain/repositories.py`)
- ✅ `UserRepository` - User Repository Interface (abstract)
  - `find_by_email()`
  - `find_by_id()`
  - `save()`

#### **Domain Events** (`domain/events.py`)
- ✅ `RoleAssigned`
- ✅ `RoleRevoked`
- ✅ `AccessChecked`
- ✅ `MembershipCreated`

---

### **Application Layer**

#### **Use Cases** (`application/use_cases.py`)
- ✅ `AssignRoleUseCase` - Role zuweisen
- ✅ `RevokeRoleUseCase` - Role entziehen
- ✅ `CheckAccessUseCase` - Zugriff prüfen
- ✅ `GetUserPermissionsUseCase` - User-Permissions abrufen
- ✅ `CreateUserUseCase` - User erstellen
- ✅ `AddMembershipUseCase` - Group-Membership hinzufügen

#### **Auth Login Service** (`application/auth_login_service.py`)
- ✅ `AuthLoginService.login()` - Login-Implementierung
- ✅ `_create_token_data()` - JWT Token erstellen
- ⚠️ **Problem:** `_get_user_permissions()` gibt nur für `qms.admin` Permissions zurück
- ⚠️ **Problem:** `_get_user_groups()` gibt leere Liste zurück (TODO)

#### **Ports** (`application/ports.py`)
- ✅ `UserRepository` Protocol
- ✅ `RoleRepository` Protocol
- ✅ `PermissionRepository` Protocol
- ✅ `AssignmentRepository` Protocol
- ✅ `MembershipRepository` Protocol
- ✅ `PolicyPort` Protocol
- ✅ `AuditPort` Protocol
- ✅ Legacy Integration Ports (für Migration)

---

### **Infrastructure Layer**

#### **Repositories** (`infrastructure/repositories.py`)
- ✅ `UserRepositoryImpl` - SQLAlchemy-Implementierung
  - Mappt `backend.app.models.User` → `DomainUser`
  - ⚠️ **Problem:** `approval_level` wird NICHT aus DB gemappt (Domain Entity hat Feld, aber nicht aus UserGroupMembership)

#### **Adapters** (`infrastructure/adapters.py`)
- ✅ Legacy Adapters für Migration
- ✅ `get_user_by_id()`, `get_user_by_email()`

#### **Auth Adapter** (`infrastructure/auth_adapter.py`)
- ✅ JWT-Token-Verwaltung

---

### **Interface Layer**

#### **Guard Router** (`interface/guard_router.py`)
- ✅ `get_current_user()` - JWT-Verifizierung und User-Extraktion
- ✅ `POST /api/auth/login` - Login-Endpoint
- ✅ `GET /api/auth/me` - User-Info-Endpoint
- ✅ `GET /api/auth/capabilities` - Capabilities-Endpoint

**Aktuelles Token-Format:**
```python
{
    "sub": str(user.id),
    "email": user.email,
    "full_name": user.full_name,
    "is_active": user.is_active,
    "user_id": user.id,
    "groups": [],  # ⚠️ LEER!
    "permissions": []  # ⚠️ Nur für qms.admin gefüllt!
}
```

---

## ❌ Was fehlt / Probleme

### **Kritische Probleme:**

1. **User.approval_level wird nicht verwendet:**
   - Domain Entity hat `approval_level` Feld
   - Aber tatsächliches Level kommt aus `UserGroupMembership.approval_level`
   - Domain Entity wird nicht korrekt aus DB gemappt (fehlt `approval_level`)

2. **Token enthält keine User-Level-Information:**
   - `user_level` fehlt im Token
   - `is_qms_admin` fehlt im Token
   - `interest_group_ids` fehlt im Token

3. **AuthLoginService._get_user_groups() gibt leere Liste zurück:**
   - TODO-Kommentar vorhanden
   - Muss aus `UserGroupMembership` geladen werden

4. **AuthLoginService._get_user_permissions() gibt nur für qms.admin Permissions zurück:**
   - Alle anderen User bekommen leeres Array
   - Muss basierend auf User-Level gefüllt werden

---

## 🎯 Was wir für Phase 1 benötigen

### **1. User-Level-Berechnung (NEU)**

**Service:** `UserLevelService` (neu in Application Layer)

```python
class UserLevelService:
    """Service zur Berechnung des User-Levels"""
    
    def get_user_level(self, user_id: int, db: Session) -> int:
        """
        Berechnet User-Level:
        - Level 5: User.is_qms_admin = True
        - Level 1-4: Höchstes approval_level aus UserGroupMembership
        - Level 0: Kein Zugriff
        """
        # Prüfe QMS Admin
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_qms_admin:
            return 5
        
        # Hole höchstes approval_level
        membership = (
            db.query(UserGroupMembership)
            .filter(UserGroupMembership.user_id == user_id)
            .order_by(UserGroupMembership.approval_level.desc())
            .first()
        )
        
        return membership.approval_level if membership else 0
    
    def get_user_interest_groups(self, user_id: int, db: Session) -> List[int]:
        """Holt alle Interest Group IDs eines Users"""
        memberships = (
            db.query(UserGroupMembership)
            .filter(
                UserGroupMembership.user_id == user_id,
                UserGroupMembership.is_active == True
            )
            .all()
        )
        return [m.interest_group_id for m in memberships]
```

### **2. AuthLoginService erweitern**

**Datei:** `contexts/accesscontrol/application/auth_login_service.py`

**Änderungen:**
1. `_create_token_data()` erweitern:
   ```python
   def _create_token_data(self, user: User) -> Dict[str, Any]:
       # User-Level berechnen (via UserLevelService)
       user_level = self._get_user_level(user.id)
       interest_group_ids = self._get_user_interest_groups(user.id)
       
       return {
           "sub": str(user.id),
           "email": user.email,
           "full_name": user.full_name,
           "is_active": user.is_active,
           "user_id": user.id,
           "user_level": user_level,  # NEU
           "is_qms_admin": self._is_qms_admin(user),  # NEU
           "interest_group_ids": interest_group_ids,  # NEU
           "groups": self._get_user_groups(user),  # Muss implementiert werden
           "permissions": self._get_user_permissions(user)  # Muss erweitert werden
       }
   ```

2. Neue Methoden:
   - `_get_user_level(user_id)` - Nutzt UserLevelService
   - `_get_user_interest_groups(user_id)` - Nutzt UserLevelService
   - `_is_qms_admin(user)` - Prüft `User.is_qms_admin`

3. `_get_user_groups()` implementieren:
   - Lädt aus `UserGroupMembership`
   - Gibt Liste von Group IDs zurück

4. `_get_user_permissions()` erweitern:
   - Basierend auf User-Level Permissions zurückgeben
   - Nicht nur für qms.admin

---

## 📋 Anpassungen am TDD-Plan

### **Phase 1 muss angepasst werden:**

**Vor Phase 1:**
1. ✅ UserLevelService erstellen (neu)
2. ✅ Tests für UserLevelService (RED)
3. ✅ UserLevelService implementieren (GREEN)

**Dann Phase 1:**
1. ✅ Tests für Token-Erweiterung (RED)
2. ✅ AuthLoginService erweitern (GREEN)

---

## 🔄 Integrations-Punkte

### **Bereits verwendet in anderen Contexts:**

1. **documentupload/interface/router.py:**
   - Nutzt `get_current_user()` aus `accesscontrol`
   - Prüft `current_user.get('email')` für QMS Admin
   - Prüft `UserGroupMembership.approval_level` für Level 4+

2. **documentupload/infrastructure/permission_service.py:**
   - `SQLAlchemyWorkflowPermissionService.get_user_level()` - **Bereits vorhanden!**
   - Können wir wiederverwenden!

---

## ✅ Empfehlung für Phase 1

**Option A: Bestehenden Service nutzen (EMPFOHLEN)**
- `SQLAlchemyWorkflowPermissionService.get_user_level()` bereits vorhanden
- `SQLAlchemyWorkflowPermissionService.get_user_interest_groups()` bereits vorhanden (TODO)
- Nutzen wir diese Services im AuthLoginService

**Option B: Neuen Service im accesscontrol Context erstellen**
- Sauberer DDD-Ansatz (alle Auth-Logik in accesscontrol)
- Keine Dependency auf documentupload Context
- Aber: Code-Duplikation möglich

**Empfehlung:** Option A - Bestehenden Service nutzen, aber in `accesscontrol` Context verschieben später

---

## 📝 Fazit

**Gut:**
- ✅ Vollständige DDD-Architektur vorhanden
- ✅ Policies, Entities, Value Objects vollständig
- ✅ Use Cases definiert
- ✅ Repository Interfaces vorhanden

**Zu tun:**
- ⚠️ AuthLoginService erweitern (Token-Daten)
- ⚠️ User-Level-Berechnung integrieren
- ⚠️ Interest Groups aus DB laden
- ⚠️ Permissions basierend auf Level zurückgeben

**Nächster Schritt:** Phase 1 anpassen und starten!

