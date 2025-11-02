# 🧪 RBAC TDD-Implementierungsplan

> **Status:** Angepasst nach AccessControl-Analyse  
> **Stand:** 2025-01-XX  
> **Version:** 1.1  
> **Methode:** Test-Driven Development (RED → GREEN → REFACTOR)  
> **Strategie:** Wiederverwendung von `SQLAlchemyWorkflowPermissionService` (Option A)

---

## 🎯 Übersicht

Dieser Plan beschreibt die schrittweise TDD-Implementierung des RBAC-Systems gemäß `docs/RBAC_SPECIFICATION.md`.

**Prinzip:** Jede Phase folgt dem TDD-Workflow:
1. **RED:** Tests schreiben (sie schlagen fehl)
2. **GREEN:** Code implementieren (Tests werden grün)
3. **REFACTOR:** Code optimieren (Tests bleiben grün)

---

## 📋 Phase 1: Backend - User-Level im JWT Token

**Ziel:** User-Level und Interest Groups werden beim Login im JWT Token mitgesendet.

**Strategie:** Nutzen des bestehenden `SQLAlchemyWorkflowPermissionService` aus `documentupload` Context.

### **1.0 Vorbereitung: get_user_interest_groups() implementieren**

**Datei:** `contexts/documentupload/infrastructure/permission_service.py`

**Aktueller Stand:** `get_user_interest_groups()` hat TODO-Kommentar, gibt leere Liste zurück.

**1.0.1 RED: Tests schreiben**

**Datei:** `tests/unit/documentupload/test_permission_service.py` (erweitern)

```python
def test_get_user_interest_groups_level_4_returns_empty_list(permission_service, mock_db, regular_user):
    """Level 4+ User bekommt leere Liste (alle IG)"""
    # Arrange
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    mock_db.query.return_value.filter.return_value.all.return_value = []
    regular_user.is_qms_admin = False
    
    # Mock: get_user_level() returns 4
    permission_service.get_user_level = MagicMock(return_value=4)
    
    # Act
    result = permission_service.get_user_interest_groups(regular_user.id)
    
    # Assert
    assert result == []  # Leere Liste = alle IG

def test_get_user_interest_groups_level_3_returns_user_ig(permission_service, mock_db, regular_user):
    """Level 3 User bekommt nur seine Interest Groups"""
    # Arrange
    membership1 = MagicMock(spec=UserGroupMembership)
    membership1.interest_group_id = 1
    membership1.is_active = True
    
    membership2 = MagicMock(spec=UserGroupMembership)
    membership2.interest_group_id = 2
    membership2.is_active = True
    
    # Mock: get_user_level() returns 3
    permission_service.get_user_level = MagicMock(return_value=3)
    
    # Mock: Query für Memberships
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [membership1, membership2]
    mock_db.query.return_value = mock_query
    
    # Act
    result = permission_service.get_user_interest_groups(regular_user.id)
    
    # Assert
    assert len(result) == 2
    assert 1 in result
    assert 2 in result

def test_get_user_interest_groups_only_active_memberships(permission_service, mock_db, regular_user):
    """Nur aktive Memberships werden zurückgegeben"""
    # Arrange
    active_membership = MagicMock()
    active_membership.interest_group_id = 1
    active_membership.is_active = True
    
    inactive_membership = MagicMock()
    inactive_membership.interest_group_id = 2
    inactive_membership.is_active = False
    
    permission_service.get_user_level = MagicMock(return_value=2)
    
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [active_membership, inactive_membership]
    mock_db.query.return_value = mock_query
    
    # Act
    result = permission_service.get_user_interest_groups(regular_user.id)
    
    # Assert
    assert len(result) == 1
    assert 1 in result
    assert 2 not in result
```

**1.0.2 GREEN: Implementierung**

```python
def get_user_interest_groups(self, user_id: int) -> List[int]:
    """
    Hole Interest Groups eines Users.
    
    Args:
        user_id: User ID
        
    Returns:
        - Level 4-5: Leere Liste (alle IG = keine Filterung)
        - Level 1-3: Liste der Interest Group IDs aus UserGroupMembership
    """
    user_level = self.get_user_level(user_id)
    
    # Level 4-5: Alle Interest Groups (keine Filterung)
    if user_level >= 4:
        return []
    
    # Level 1-3: Nur eigene Interest Groups
    memberships = (
        self.db.query(UserGroupMembership)
        .filter(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.is_active == True
        )
        .all()
    )
    
    return [m.interest_group_id for m in memberships]
```

### **1.1 RED: Tests schreiben**

**Datei:** `tests/unit/accesscontrol/test_auth_login_service.py`

```python
import pytest
from jose import jwt
from contexts.accesscontrol.application.auth_login_service import AuthLoginService
from contexts.accesscontrol.infrastructure.repositories import UserRepositoryImpl
from backend.app.database import SessionLocal
from backend.app.models import User, UserGroupMembership, InterestGroup

def decode_jwt(token: str) -> dict:
    """Hilfsfunktion zum Decodieren von JWT"""
    secret_key = "test-secret-123"
    return jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_signature": False})

def test_login_returns_user_level_5_for_qms_admin(db_session):
    """Level 5 (QMS Admin) sollte Level 5 im Token haben"""
    # Arrange
    admin_user = User(
        email="qms.admin@company.com",
        full_name="QMS Admin",
        hashed_password="hashed",  # Für Test
        is_qms_admin=True,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    
    user_repo = UserRepositoryImpl(db_session)
    auth_service = AuthLoginService(user_repo)
    
    # Act
    result = auth_service.login("qms.admin@company.com", "Admin!234")
    
    # Assert
    assert result.success
    token_data = decode_jwt(result.data["access_token"])
    assert token_data["user_level"] == 5
    assert token_data["is_qms_admin"] is True
    assert token_data["interest_group_ids"] == []  # Level 5 = alle IG

def test_login_returns_user_level_from_membership(db_session):
    """User ohne is_qms_admin sollte höchstes approval_level aus Memberships bekommen"""
    # Arrange
    user = User(
        email="qm.mitarbeiter@company.com",
        full_name="QM Mitarbeiter",
        hashed_password="hashed",
        is_qms_admin=False,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Interest Group erstellen
    qm_group = InterestGroup(name="Qualitätsmanagement", code="QM", is_active=True)
    db_session.add(qm_group)
    db_session.flush()
    
    # Membership erstellen
    membership = UserGroupMembership(
        user_id=user.id,
        interest_group_id=qm_group.id,
        approval_level=4,
        is_active=True
    )
    db_session.add(membership)
    db_session.commit()
    
    user_repo = UserRepositoryImpl(db_session)
    auth_service = AuthLoginService(user_repo)
    
    # Act
    result = auth_service.login("qm.mitarbeiter@company.com", "123")
    
    # Assert
    assert result.success
    token_data = decode_jwt(result.data["access_token"])
    assert token_data["user_level"] == 4
    assert token_data["is_qms_admin"] is False
    assert token_data["interest_group_ids"] == [qm_group.id]

def test_login_returns_interest_groups_in_token(db_session):
    """Token sollte alle Interest Group IDs des Users enthalten"""
    # Arrange
    user = User(email="user@company.com", full_name="Test User", hashed_password="hashed", is_active=True)
    db_session.add(user)
    db_session.flush()
    
    qm_group = InterestGroup(name="Qualitätsmanagement", code="QM", is_active=True)
    sv_group = InterestGroup(name="Service", code="SV", is_active=True)
    db_session.add(qm_group)
    db_session.add(sv_group)
    db_session.flush()
    
    membership1 = UserGroupMembership(user_id=user.id, interest_group_id=qm_group.id, approval_level=3, is_active=True)
    membership2 = UserGroupMembership(user_id=user.id, interest_group_id=sv_group.id, approval_level=2, is_active=True)
    db_session.add(membership1)
    db_session.add(membership2)
    db_session.commit()
    
    user_repo = UserRepositoryImpl(db_session)
    auth_service = AuthLoginService(user_repo)
    
    # Act
    result = auth_service.login("user@company.com", "123")
    
    # Assert
    assert result.success
    token_data = decode_jwt(result.data["access_token"])
    assert "interest_group_ids" in token_data
    assert len(token_data["interest_group_ids"]) == 2
    assert qm_group.id in token_data["interest_group_ids"]
    assert sv_group.id in token_data["interest_group_ids"]

def test_login_returns_highest_level_when_multiple_memberships(db_session):
    """User mit mehreren Memberships sollte höchstes Level bekommen"""
    # Arrange
    user = User(email="user@company.com", full_name="Test User", hashed_password="hashed", is_active=True)
    db_session.add(user)
    db_session.flush()
    
    sv_group = InterestGroup(name="Service", code="SV", is_active=True)
    qm_group = InterestGroup(name="Qualitätsmanagement", code="QM", is_active=True)
    db_session.add(sv_group)
    db_session.add(qm_group)
    db_session.flush()
    
    membership1 = UserGroupMembership(user_id=user.id, interest_group_id=sv_group.id, approval_level=2, is_active=True)
    membership2 = UserGroupMembership(user_id=user.id, interest_group_id=qm_group.id, approval_level=4, is_active=True)
    db_session.add(membership1)
    db_session.add(membership2)
    db_session.commit()
    
    user_repo = UserRepositoryImpl(db_session)
    auth_service = AuthLoginService(user_repo)
    
    # Act
    result = auth_service.login("user@company.com", "123")
    
    # Assert
    assert result.success
    token_data = decode_jwt(result.data["access_token"])
    assert token_data["user_level"] == 4  # Höchstes Level
```

### **1.2 GREEN: Implementierung**

**Datei:** `contexts/accesscontrol/application/auth_login_service.py`

**Änderungen:**

1. **Import hinzufügen:**
```python
from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
from backend.app.database import SessionLocal
```

2. **AuthLoginService erweitern:**
```python
class AuthLoginService:
    """Service für Authentifizierung im DDD-Modus"""
    
    def __init__(self, user_repository: UserRepository, db_session: Optional[Session] = None):
        self.user_repository = user_repository
        self.secret_key = os.getenv("SECRET_KEY", "test-secret-123")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.db_session = db_session  # NEU: Für Permission Service
        
    def _get_user_level(self, user_id: int) -> int:
        """Berechnet User-Level via SQLAlchemyWorkflowPermissionService"""
        if not self.db_session:
            # Fallback: DB Session holen
            db = next(SessionLocal())
            try:
                permission_service = SQLAlchemyWorkflowPermissionService(db)
                return permission_service.get_user_level(user_id)
            finally:
                db.close()
        else:
            permission_service = SQLAlchemyWorkflowPermissionService(self.db_session)
            return permission_service.get_user_level(user_id)
    
    def _get_user_interest_groups(self, user_id: int) -> List[int]:
        """Holt Interest Groups via SQLAlchemyWorkflowPermissionService"""
        if not self.db_session:
            db = next(SessionLocal())
            try:
                permission_service = SQLAlchemyWorkflowPermissionService(db)
                return permission_service.get_user_interest_groups(user_id)
            finally:
                db.close()
        else:
            permission_service = SQLAlchemyWorkflowPermissionService(self.db_session)
            return permission_service.get_user_interest_groups(user_id)
    
    def _is_qms_admin(self, user: User) -> bool:
        """Prüft ob User QMS Admin ist"""
        # Prüfe is_qms_admin aus DB (nicht Domain Entity!)
        if not self.db_session:
            db = next(SessionLocal())
            try:
                db_user = db.query(User).filter(User.id == user.id).first()
                return db_user.is_qms_admin if db_user else False
            finally:
                db.close()
        else:
            db_user = self.db_session.query(User).filter(User.id == user.id).first()
            return db_user.is_qms_admin if db_user else False
    
    def _create_token_data(self, user: User) -> Dict[str, Any]:
        """Erstellt Token-Daten (erweitert mit User-Level)"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        # User-Level und Interest Groups berechnen
        user_level = self._get_user_level(user.id)
        is_qms_admin = self._is_qms_admin(user)
        interest_group_ids = self._get_user_interest_groups(user.id)
        
        return {
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "iat": now,
            "exp": expire,
            "user_id": user.id,
            "user_level": user_level,  # NEU
            "is_qms_admin": is_qms_admin,  # NEU
            "interest_group_ids": interest_group_ids,  # NEU
            "groups": self._get_user_groups(user),
            "permissions": self._get_user_permissions(user)
        }
```

3. **AuthLoginService.__init__() anpassen (DB Session übergeben):**

**Datei:** `contexts/accesscontrol/interface/guard_router.py` (Login-Endpoint)

```python
@router.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint - Authenticate user and return JWT token.
    """
    # Initialize repository and service WITH DB SESSION
    user_repo = UserRepositoryImpl(db)
    auth_service = AuthLoginService(user_repo, db_session=db)  # NEU: db_session übergeben
    
    try:
        result = auth_service.login(request.email, request.password)
        # ... rest of implementation
```

### **1.3 REFACTOR: Code optimieren**

- **DB Session Management:** AuthLoginService sollte DB Session über Dependency Injection bekommen (nicht selbst erstellen)
- **Performance:** Query nur einmal ausführen (Level + IG in einem Query möglich)
- **Error Handling:** Fehlerbehandlung für fehlende Memberships
- **Tests:** Integration Tests hinzufügen

### **1.4 Checklist**

- [ ] **1.0:** `get_user_interest_groups()` implementiert (in permission_service.py)
- [ ] **1.0:** Tests für `get_user_interest_groups()` geschrieben (RED)
- [ ] **1.0:** Tests grün (GREEN)
- [ ] **1.1:** Unit Tests für AuthLoginService geschrieben (RED)
- [ ] **1.1:** Tests schlagen fehl (erwartetes Verhalten)
- [ ] **1.2:** `_get_user_level()` implementiert (nutzt SQLAlchemyWorkflowPermissionService)
- [ ] **1.2:** `_get_user_interest_groups()` implementiert (nutzt SQLAlchemyWorkflowPermissionService)
- [ ] **1.2:** `_is_qms_admin()` implementiert
- [ ] **1.2:** `_create_token_data()` erweitert
- [ ] **1.2:** Login-Endpoint angepasst (DB Session übergeben)
- [ ] **1.2:** Alle Tests grün (GREEN)
- [ ] **1.3:** Integration Tests geschrieben
- [ ] **1.3:** Code refactored (DB Session Management)
- [ ] **1.3:** Tests bleiben grün (REFACTOR)

---

## 📋 Phase 2: Backend - Interest Group Filtering (RAG Chat)

**Ziel:** RAG Chat-Endpunkte filtern Dokumente basierend auf User-Level und Interest Groups.

### **2.1 RED: Tests schreiben**

**Datei:** `tests/integration/ragintegration/test_rag_interest_group_filtering.py`

```python
def test_rag_chat_level_1_only_sees_own_interest_group():
    """Level 1 User sieht nur Dokumente aus seiner Interest Group"""
    # Arrange
    user = create_test_user(level=1, interest_groups=["SV"])
    create_document("doc1", interest_groups=["SV"], status="approved")
    create_document("doc2", interest_groups=["IT"], status="approved")
    
    # Act
    response = rag_service.ask_question(user.id, "Test question")
    
    # Assert
    # Nur doc1 sollte in den Source References sein
    assert any(ref.document_id == doc1.id for ref in response.source_references)
    assert not any(ref.document_id == doc2.id for ref in response.source_references)

def test_rag_chat_level_4_sees_all_documents():
    """Level 4 User sieht alle Dokumente (keine IG-Filterung)"""
    # Arrange
    user = create_test_user(level=4, interest_groups=["QM"])
    create_document("doc1", interest_groups=["SV"], status="approved")
    create_document("doc2", interest_groups=["IT"], status="approved")
    
    # Act
    response = rag_service.ask_question(user.id, "Test question")
    
    # Assert
    # Beide Dokumente sollten sichtbar sein
    assert len(response.source_references) >= 2

def test_rag_search_level_3_only_sees_own_interest_group():
    """Level 3 User sieht nur Dokumente aus seiner Interest Group"""
    # Arrange
    user = create_test_user(level=3, interest_groups=["SV"])
    create_document("doc1", interest_groups=["SV"], status="approved")
    create_document("doc2", interest_groups=["IT"], status="approved")
    
    # Act
    results = rag_service.search_documents(user.id, "test query")
    
    # Assert
    assert len(results) == 1
    assert results[0].document_id == doc1.id
```

### **2.2 GREEN: Implementierung**

**Datei:** `contexts/ragintegration/application/use_cases.py` (AskQuestionUseCase)

**Änderungen:**
1. `AskQuestionUseCase.execute()` erweitern:
   - User-Level aus Permission Service holen
   - Interest Group IDs aus User holen (wenn Level < 4)
   - Vector Search Filter anwenden (wenn Level < 4)

2. Neuer Service: `InterestGroupFilterService`:
   - `filter_documents_by_interest_group(user_id, document_ids)` → gefilterte IDs
   - Level 1-3: Nur eigene IG
   - Level 4-5: Keine Filterung

3. `QdrantVectorStoreAdapter.search()` erweitern:
   - Optional: Interest Group Filter als Parameter
   - Filter wird auf Chunk-Level angewendet (via Metadata)

**Datei:** `contexts/ragintegration/infrastructure/repositories.py`

**Änderungen:**
- `SQLAlchemyIndexedDocumentRepository.get_by_ids()` erweitern:
  - Optional: Interest Group Filter

### **2.3 REFACTOR: Code optimieren**

- Performance: Filter-Query optimieren (Index auf `interest_group_id`)
- Caching: Interest Groups pro User cachen
- Tests: Edge Cases (keine IG, mehrere IG)

### **2.4 Checklist**

- [ ] Unit Tests geschrieben (RED)
- [ ] Integration Tests geschrieben (RED)
- [ ] Tests schlagen fehl
- [ ] `InterestGroupFilterService` implementiert
- [ ] `AskQuestionUseCase` erweitert
- [ ] Vector Store Filter implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored
- [ ] Performance-Tests hinzugefügt

---

## 📋 Phase 3: Backend - Interest Group Filtering (Dokumenten-Liste)

**Ziel:** Dokumenten-Liste-Endpunkt filtert basierend auf User-Level.

### **3.1 RED: Tests schreiben**

**Datei:** `tests/integration/documentupload/test_document_list_filtering.py`

```python
def test_document_list_level_1_only_sees_own_interest_group():
    """Level 1 User sieht nur Dokumente aus seiner Interest Group"""
    # Arrange
    user = create_test_user(level=1, interest_groups=["SV"])
    create_document("doc1", interest_groups=["SV"])
    create_document("doc2", interest_groups=["IT"])
    
    # Act
    response = client.get("/api/document-upload/", headers=auth_header(user))
    
    # Assert
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "doc1"

def test_document_list_level_4_sees_all_documents():
    """Level 4 User sieht alle Dokumente"""
    # Arrange
    user = create_test_user(level=4, interest_groups=["QM"])
    create_document("doc1", interest_groups=["SV"])
    create_document("doc2", interest_groups=["IT"])
    
    # Act
    response = client.get("/api/document-upload/", headers=auth_header(user))
    
    # Assert
    assert len(response.json()) >= 2
```

### **3.2 GREEN: Implementierung**

**Datei:** `contexts/documentupload/interface/router.py` (GET /api/document-upload/)

**Änderungen:**
1. Endpoint erweitern:
   - User-Level aus Permission Service holen
   - Wenn Level < 4: Interest Group Filter anwenden
   - Query filtert nach `upload_document_interest_groups.interest_group_id IN (user_ig_ids)`

2. Query anpassen:
```python
if user_level < 4:
    # Filter by user's interest groups
    query = query.join(
        UploadDocumentInterestGroup
    ).filter(
        UploadDocumentInterestGroup.interest_group_id.in_(user_interest_group_ids)
    )
```

### **3.3 REFACTOR: Code optimieren**

- Query optimieren (INNER JOIN statt Subquery)
- Index auf `interest_group_id` prüfen
- Pagination berücksichtigen

### **3.4 Checklist**

- [ ] Integration Tests geschrieben (RED)
- [ ] Tests schlagen fehl
- [ ] Endpoint erweitert
- [ ] Query-Filter implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored
- [ ] Performance-Tests

---

## 📋 Phase 4: Frontend - User-Level Extraction

**Ziel:** Frontend extrahiert User-Level und Interest Groups aus JWT Token.

### **4.1 RED: Tests schreiben**

**Datei:** `frontend/test/lib/test_userContext.tsx`

```typescript
describe('UserContext', () => {
  it('should extract user level 5 from JWT token', () => {
    const token = createMockToken({ user_level: 5, is_qms_admin: true })
    sessionStorage.setItem('access_token', token)
    
    const { result } = renderHook(() => useUser())
    
    expect(result.current.userLevel).toBe(5)
    expect(result.current.isQmsAdmin).toBe(true)
  })

  it('should extract user level from membership', () => {
    const token = createMockToken({ user_level: 4, is_qms_admin: false })
    sessionStorage.setItem('access_token', token)
    
    const { result } = renderHook(() => useUser())
    
    expect(result.current.userLevel).toBe(4)
    expect(result.current.isQmsAdmin).toBe(false)
  })

  it('should extract interest group IDs', () => {
    const token = createMockToken({ 
      user_level: 3,
      interest_group_ids: [1, 2, 3]
    })
    sessionStorage.setItem('access_token', token)
    
    const { result } = renderHook(() => useUser())
    
    expect(result.current.interestGroupIds).toEqual([1, 2, 3])
  })
})
```

### **4.2 GREEN: Implementierung**

**Datei:** `frontend/lib/contexts/UserContext.tsx` (neu oder erweitern)

**Implementierung:**
```typescript
interface UserContextType {
  userLevel: number
  isQmsAdmin: boolean
  interestGroupIds: number[]
  hasPermission: (requiredLevel: number) => boolean
  canAccess: (feature: string) => boolean
}

export function UserProvider({ children }) {
  const [userLevel, setUserLevel] = useState(0)
  const [isQmsAdmin, setIsQmsAdmin] = useState(false)
  const [interestGroupIds, setInterestGroupIds] = useState<number[]>([])

  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        setUserLevel(payload.user_level || 0)
        setIsQmsAdmin(payload.is_qms_admin || false)
        setInterestGroupIds(payload.interest_group_ids || [])
      } catch (e) {
        console.error('Failed to parse token:', e)
      }
    }
  }, [])

  const hasPermission = (requiredLevel: number) => {
    return userLevel >= requiredLevel
  }

  const canAccess = (feature: string) => {
    // Feature-basierte Berechtigungen
    const featureMap = {
      'users': userLevel === 5,
      'upload': userLevel >= 4,
      'kanban': userLevel >= 3,
      'prompt-management': userLevel === 5,
      'ai-models': userLevel === 5,
    }
    return featureMap[feature] || false
  }

  return (
    <UserContext.Provider value={{
      userLevel,
      isQmsAdmin,
      interestGroupIds,
      hasPermission,
      canAccess
    }}>
      {children}
    </UserContext.Provider>
  )
}
```

**Datei:** `frontend/app/layout.tsx`

**Änderung:**
```typescript
<UserProvider>
  <DashboardProvider>
    {children}
  </DashboardProvider>
</UserProvider>
```

### **4.3 REFACTOR: Code optimieren**

- Token-Refresh Handling
- Error Handling für ungültige Tokens
- TypeScript Types verbessern

### **4.4 Checklist**

- [ ] Unit Tests geschrieben (RED)
- [ ] Tests schlagen fehl
- [ ] `UserContext` implementiert
- [ ] `useUser()` Hook erstellt
- [ ] Token-Parsing implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Integration in `layout.tsx`
- [ ] Code refactored

---

## 📋 Phase 5: Frontend - Navigation Filtering

**Ziel:** Navigation-Links werden basierend auf User-Level ausgeblendet.

### **5.1 RED: Tests schreiben**

**Datei:** `frontend/test/components/Navigation.test.tsx`

```typescript
describe('Navigation', () => {
  it('should hide "Benutzer" link for level 4 user', () => {
    const token = createMockToken({ user_level: 4 })
    sessionStorage.setItem('access_token', token)
    
    render(<Navigation />)
    
    expect(screen.queryByText('Benutzer')).not.toBeInTheDocument()
    expect(screen.getByText('Dokument Upload')).toBeInTheDocument()
  })

  it('should hide "Dokument Upload" for level 3 user', () => {
    const token = createMockToken({ user_level: 3 })
    sessionStorage.setItem('access_token', token)
    
    render(<Navigation />)
    
    expect(screen.queryByText('Dokument Upload')).not.toBeInTheDocument()
    expect(screen.getByText('Dokumente')).toBeInTheDocument()
  })

  it('should show only "Home" for level 1 user', () => {
    const token = createMockToken({ user_level: 1 })
    sessionStorage.setItem('access_token', token)
    
    render(<Navigation />)
    
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.queryByText('Dokumente')).not.toBeInTheDocument()
    expect(screen.queryByText('Prompt-Verwaltung')).not.toBeInTheDocument()
  })

  it('should show level badge in navigation', () => {
    const token = createMockToken({ user_level: 4 })
    sessionStorage.setItem('access_token', token)
    
    render(<Navigation />)
    
    expect(screen.getByText('Level 4')).toBeInTheDocument()
  })
})
```

### **5.2 GREEN: Implementierung**

**Datei:** `frontend/app/components/Navigation.tsx`

**Änderungen:**
```typescript
export default function Navigation() {
  const { userLevel, canAccess } = useUser()
  const pathname = usePathname()

  // Navigation Links mit Permission-Check
  const navLinks = [
    { href: '/', label: 'Home', icon: Home, requiredLevel: 1 },
    { href: '/document-upload', label: 'Dokument Upload', icon: FileText, requiredLevel: 4 },
    { href: '/documents', label: 'Dokumente', icon: FileText, requiredLevel: 2 },
    { href: '/prompt-management', label: 'Prompt-Verwaltung', icon: Settings, requiredLevel: 5 },
    { href: '/models', label: 'AI Models', icon: BarChart3, requiredLevel: 5 },
    { href: '/users', label: 'Benutzer', icon: Users, requiredLevel: 5 },
  ].filter(link => userLevel >= link.requiredLevel)

  return (
    <nav>
      {/* ... */}
      {navLinks.map((link) => (
        <Link key={link.href} href={link.href}>
          {link.label}
        </Link>
      ))}
      
      {/* Level Badge */}
      <div className="text-sm text-gray-500">
        Level {userLevel}
      </div>
    </nav>
  )
}
```

### **5.3 REFACTOR: Code optimieren**

- Badge-Styling verbessern
- Tooltips für disabled Links (falls später benötigt)
- Icon-Import optimieren

### **5.4 Checklist**

- [ ] Unit Tests geschrieben (RED)
- [ ] Tests schlagen fehl
- [ ] Navigation-Filter implementiert
- [ ] Level-Badge hinzugefügt
- [ ] Alle Tests grün (GREEN)
- [ ] UI-Tests (Browser)
- [ ] Code refactored

---

## 📋 Phase 6: Frontend - Dokumenten-Upload Seite (Level 4+)

**Ziel:** Upload-Seite nur für Level 4+ sichtbar.

### **6.1 RED: Tests schreiben**

**Datei:** `frontend/test/app/document-upload/page.test.tsx`

```typescript
describe('DocumentUploadPage', () => {
  it('should redirect level 3 user to home', () => {
    const token = createMockToken({ user_level: 3 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentUploadPage />)
    
    expect(mockRouter.push).toHaveBeenCalledWith('/')
  })

  it('should show upload form for level 4 user', () => {
    const token = createMockToken({ user_level: 4 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentUploadPage />)
    
    expect(screen.getByText('Dokument hochladen')).toBeInTheDocument()
  })
})
```

### **6.2 GREEN: Implementierung**

**Datei:** `frontend/app/document-upload/page.tsx`

**Änderungen:**
```typescript
export default function DocumentUploadPage() {
  const router = useRouter()
  const { userLevel } = useUser()

  useEffect(() => {
    if (userLevel < 4) {
      router.push('/')
    }
  }, [userLevel, router])

  if (userLevel < 4) {
    return null // Oder Loading-Spinner
  }

  // ... rest of component
}
```

### **6.3 REFACTOR: Code optimieren**

- Loading-State während Redirect
- Error-Handling

### **6.4 Checklist**

- [ ] Tests geschrieben (RED)
- [ ] Redirect-Logik implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored

---

## 📋 Phase 7: Frontend - Dokumenten-Seite (Kanban vs. Tabelle)

**Ziel:** Level 2 sieht nur Tabelle, Level 3+ sieht Kanban.

### **7.1 RED: Tests schreiben**

**Datei:** `frontend/test/app/documents/page.test.tsx`

```typescript
describe('DocumentListPage', () => {
  it('should show only table view for level 2 user', () => {
    const token = createMockToken({ user_level: 2 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentListPage />)
    
    expect(screen.getByText('Tabellen-Ansicht')).toBeInTheDocument()
    expect(screen.queryByText('Kanban-Ansicht')).not.toBeInTheDocument()
  })

  it('should show kanban view for level 3 user', () => {
    const token = createMockToken({ user_level: 3 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentListPage />)
    
    expect(screen.getByText('Kanban-Ansicht')).toBeInTheDocument()
  })

  it('should default to table view for level 2', () => {
    const token = createMockToken({ user_level: 2 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentListPage />)
    
    const { viewMode } = getComponentState()
    expect(viewMode).toBe('table')
  })
})
```

### **7.2 GREEN: Implementierung**

**Datei:** `frontend/app/documents/page.tsx`

**Änderungen:**
```typescript
export default function DocumentListPage() {
  const { userLevel } = useUser()
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>(
    userLevel >= 3 ? 'kanban' : 'table'
  )

  // Kanban nur für Level 3+
  const canViewKanban = userLevel >= 3

  return (
    <div>
      {/* View Mode Toggle - nur wenn Kanban erlaubt */}
      {canViewKanban && (
        <div>
          <button onClick={() => setViewMode('kanban')}>Kanban</button>
          <button onClick={() => setViewMode('table')}>Tabelle</button>
        </div>
      )}

      {viewMode === 'kanban' && canViewKanban ? (
        <KanbanBoard />
      ) : (
        <TableView />
      )}
    </div>
  )
}
```

### **7.3 REFACTOR: Code optimieren**

- View-Mode Persistence (localStorage)
- Smooth Transition zwischen Views

### **7.4 Checklist**

- [ ] Tests geschrieben (RED)
- [ ] View-Mode-Logik implementiert
- [ ] Kanban-Toggle implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored

---

## 📋 Phase 8: Frontend - Workflow-Buttons (Level-basiert)

**Ziel:** Workflow-Buttons basierend auf User-Level aktivieren/deaktivieren.

### **8.1 RED: Tests schreiben**

**Datei:** `frontend/test/app/documents/StatusChangeModal.test.tsx`

```typescript
describe('StatusChangeModal', () => {
  it('should disable "Approved" button for level 3 user', () => {
    const token = createMockToken({ user_level: 3 })
    sessionStorage.setItem('access_token', token)
    
    render(<StatusChangeModal currentStatus="reviewed" />)
    
    const approveButton = screen.getByText('Freigeben')
    expect(approveButton).toBeDisabled()
  })

  it('should enable "Approved" button for level 4 user', () => {
    const token = createMockToken({ user_level: 4 })
    sessionStorage.setItem('access_token', token)
    
    render(<StatusChangeModal currentStatus="reviewed" />)
    
    const approveButton = screen.getByText('Freigeben')
    expect(approveButton).not.toBeDisabled()
  })

  it('should show only "Reviewed" transition for level 3', () => {
    const token = createMockToken({ user_level: 3 })
    sessionStorage.setItem('access_token', token)
    
    render(<StatusChangeModal currentStatus="draft" />)
    
    expect(screen.getByText('Als geprüft markieren')).toBeInTheDocument()
    expect(screen.queryByText('Freigeben')).not.toBeInTheDocument()
  })
})
```

### **8.2 GREEN: Implementierung**

**Datei:** `frontend/app/documents/StatusChangeModal.tsx`

**Änderungen:**
```typescript
export default function StatusChangeModal({ currentStatus, ... }) {
  const { userLevel } = useUser()
  const [allowedTransitions, setAllowedTransitions] = useState<WorkflowStatus[]>([])

  useEffect(() => {
    // Hole erlaubte Transitions vom Backend
    getAllowedTransitions(documentId).then(setAllowedTransitions)
  }, [documentId, userLevel])

  // Frontend-Filter basierend auf Level
  const canApprove = userLevel >= 4
  const canReview = userLevel >= 3

  return (
    <Modal>
      {canReview && currentStatus === 'draft' && (
        <button onClick={() => changeStatus('reviewed')}>
          Als geprüft markieren
        </button>
      )}
      {canApprove && currentStatus === 'reviewed' && (
        <>
          <button onClick={() => changeStatus('approved')}>
            Freigeben
          </button>
          <button onClick={() => changeStatus('rejected')}>
            Zurückweisen
          </button>
        </>
      )}
    </Modal>
  )
}
```

### **8.3 REFACTOR: Code optimieren**

- Tooltips für disabled Buttons
- Bessere UX (warum Button disabled ist)

### **8.4 Checklist**

- [ ] Tests geschrieben (RED)
- [ ] Button-Logik implementiert
- [ ] Transition-Filter implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored

---

## 📋 Phase 9: Frontend - Kommentar-Funktion (Level 2+)

**Ziel:** Kommentar-Funktion für Level 2+ aktivieren.

### **9.1 RED: Tests schreiben**

**Datei:** `frontend/test/app/documents/[id]/page.test.tsx`

```typescript
describe('DocumentDetailPage', () => {
  it('should show comment input for level 2 user', () => {
    const token = createMockToken({ user_level: 2 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentDetailPage documentId={1} />)
    
    expect(screen.getByPlaceholderText('Kommentar hinzufügen')).toBeInTheDocument()
  })

  it('should hide comment input for level 1 user', () => {
    const token = createMockToken({ user_level: 1 })
    sessionStorage.setItem('access_token', token)
    
    render(<DocumentDetailPage documentId={1} />)
    
    expect(screen.queryByPlaceholderText('Kommentar hinzufügen')).not.toBeInTheDocument()
  })
})
```

### **9.2 GREEN: Implementierung**

**Datei:** `frontend/app/documents/[id]/page.tsx`

**Änderungen:**
```typescript
export default function DocumentDetailPage() {
  const { userLevel } = useUser()
  const canComment = userLevel >= 2

  return (
    <div>
      {/* ... */}
      {canComment && (
        <CommentSection documentId={documentId} />
      )}
    </div>
  )
}
```

### **9.3 REFACTOR: Code optimieren**

- Kommentar-Validierung
- Real-time Updates

### **9.4 Checklist**

- [ ] Tests geschrieben (RED)
- [ ] Kommentar-Komponente implementiert
- [ ] Permission-Check implementiert
- [ ] Alle Tests grün (GREEN)
- [ ] Code refactored

---

## 📋 Phase 10: Integration Tests (E2E)

**Ziel:** End-to-End Tests für komplette RBAC-Workflows.

### **10.1 RED: Tests schreiben**

**Datei:** `tests/e2e/test_rbac_workflows.py`

```python
def test_level_1_user_workflow():
    """Level 1 User: Nur RAG Chat, keine Dokumenten-Liste"""
    # Login als Level 1
    token = login("mitarbeiter.service@company.com", "123")
    
    # RAG Chat sollte funktionieren
    response = client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "RAG Chat" in response.text
    
    # Dokumenten-Liste sollte 403/redirect geben
    response = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [403, 302]

def test_level_4_user_can_upload():
    """Level 4 User: Kann Dokumente hochladen"""
    token = login("qm.mitarbeiter@company.com", "123")
    
    # Upload sollte funktionieren
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    response = client.post(
        "/api/document-upload/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

def test_level_3_user_can_review():
    """Level 3 User: Kann Draft → Reviewed verschieben"""
    token = login("abteilungsleiter.service@company.com", "123")
    
    # Status-Änderung sollte funktionieren
    response = client.post(
        "/api/document-workflow/change-status",
        json={"document_id": 1, "new_status": "reviewed", "reason": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### **10.2 GREEN: Implementierung**

- Alle vorherigen Phasen müssen abgeschlossen sein
- Backend-Endpunkte müssen alle Permission-Checks haben
- Frontend muss alle Redirects/Filter haben

### **10.3 REFACTOR: Code optimieren**

- Test-Daten-Setup optimieren
- Test-Performance verbessern

### **10.4 Checklist**

- [ ] E2E Tests geschrieben (RED)
- [ ] Alle E2E Tests grün (GREEN)
- [ ] Test-Dokumentation erstellt
- [ ] Performance-Tests

---

## 📊 Gesamt-Übersicht

### **Phasen-Status:**

| Phase | Beschreibung | Status | Geschätzte Zeit |
|-------|--------------|--------|-----------------|
| **1** | Backend: User-Level im JWT | 🔴 TODO | 2-3h |
| **2** | Backend: RAG Chat IG-Filter | 🔴 TODO | 3-4h |
| **3** | Backend: Dokumenten-Liste IG-Filter | 🔴 TODO | 2-3h |
| **4** | Frontend: User-Level Extraction | 🔴 TODO | 2-3h |
| **5** | Frontend: Navigation Filtering | 🔴 TODO | 2-3h |
| **6** | Frontend: Upload-Seite (Level 4+) | 🔴 TODO | 1-2h |
| **7** | Frontend: Kanban vs. Tabelle | 🔴 TODO | 2-3h |
| **8** | Frontend: Workflow-Buttons | 🔴 TODO | 2-3h |
| **9** | Frontend: Kommentar-Funktion | 🔴 TODO | 1-2h |
| **10** | Integration Tests (E2E) | 🔴 TODO | 3-4h |

**Gesamt:** ~20-28 Stunden

---

## 🎯 Nächste Schritte

1. **Phase 1 starten:** Backend User-Level im JWT
2. **Test-User validieren:** Login mit allen Test-Usern testen
3. **Schrittweise durcharbeiten:** Jede Phase komplett abschließen bevor nächste beginnt

---

## 📝 Wichtige Hinweise

- **TDD-Prinzip:** Immer Tests ZUERST (RED)
- **Keine Shortcuts:** Jede Phase vollständig abschließen
- **Tests dokumentieren:** Jeder Test sollte klar sein
- **Code-Review:** Nach jeder Phase Code-Review durchführen

---

**Status:** Plan erstellt, bereit für Implementierung 🚀

