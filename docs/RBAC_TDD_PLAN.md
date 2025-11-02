# 🧪 RBAC TDD-Implementierungsplan

> **Status:** Entwurf  
> **Stand:** 2025-01-XX  
> **Version:** 1.0  
> **Methode:** Test-Driven Development (RED → GREEN → REFACTOR)

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

### **1.1 RED: Tests schreiben**

**Datei:** `tests/unit/accesscontrol/test_auth_login_service.py`

```python
def test_login_returns_user_level_5_for_qms_admin():
    """Level 5 (QMS Admin) sollte Level 5 im Token haben"""
    # Arrange
    user = create_test_user(email="qms.admin@company.com", is_qms_admin=True)
    
    # Act
    result = auth_service.login("qms.admin@company.com", "123")
    
    # Assert
    token_data = decode_jwt(result.access_token)
    assert token_data["user_level"] == 5
    assert token_data["is_qms_admin"] is True

def test_login_returns_user_level_from_membership():
    """User ohne is_qms_admin sollte höchstes approval_level aus Memberships bekommen"""
    # Arrange
    user = create_test_user(email="qm.mitarbeiter@company.com")
    create_membership(user, "QM", approval_level=4)
    
    # Act
    result = auth_service.login("qm.mitarbeiter@company.com", "123")
    
    # Assert
    token_data = decode_jwt(result.access_token)
    assert token_data["user_level"] == 4
    assert token_data["is_qms_admin"] is False

def test_login_returns_interest_groups_in_token():
    """Token sollte alle Interest Group IDs des Users enthalten"""
    # Arrange
    user = create_test_user(email="user@company.com")
    create_membership(user, "QM", approval_level=3)
    create_membership(user, "SV", approval_level=2)
    
    # Act
    result = auth_service.login("user@company.com", "123")
    
    # Assert
    token_data = decode_jwt(result.access_token)
    assert "interest_group_ids" in token_data
    assert len(token_data["interest_group_ids"]) == 2
    assert 1 in token_data["interest_group_ids"]  # QM ID
    assert 2 in token_data["interest_group_ids"]  # SV ID

def test_login_returns_highest_level_when_multiple_memberships():
    """User mit mehreren Memberships sollte höchstes Level bekommen"""
    # Arrange
    user = create_test_user(email="user@company.com")
    create_membership(user, "SV", approval_level=2)
    create_membership(user, "QM", approval_level=4)
    
    # Act
    result = auth_service.login("user@company.com", "123")
    
    # Assert
    token_data = decode_jwt(result.access_token)
    assert token_data["user_level"] == 4  # Höchstes Level
```

### **1.2 GREEN: Implementierung**

**Datei:** `contexts/accesscontrol/application/auth_login_service.py`

**Änderungen:**
1. `_create_token_data()` erweitern:
   - `user_level` berechnen (via `get_user_level()`)
   - `interest_group_ids` sammeln (aus `UserGroupMembership`)
   - `is_qms_admin` Flag hinzufügen

2. Neue Methode `_get_user_level(user)`:
   - Prüft `user.is_qms_admin` → Level 5
   - Sonst: Höchstes `approval_level` aus `UserGroupMembership`
   - Sonst: Level 0

3. Neue Methode `_get_user_interest_groups(user)`:
   - Sammelt alle `interest_group_id` aus aktiven Memberships

**Dependencies:**
- Zugriff auf `backend.app.models.UserGroupMembership`
- Database Session (über Repository)

### **1.3 REFACTOR: Code optimieren**

- Performance: Query nur einmal ausführen (Memberships + Level in einem Query)
- Error Handling: Fehlerbehandlung für fehlende Memberships
- Tests: Integration Tests hinzufügen

### **1.4 Checklist**

- [ ] Unit Tests geschrieben (RED)
- [ ] Tests schlagen fehl (erwartetes Verhalten)
- [ ] `_get_user_level()` implementiert
- [ ] `_get_user_interest_groups()` implementiert
- [ ] `_create_token_data()` erweitert
- [ ] Alle Tests grün (GREEN)
- [ ] Integration Tests geschrieben
- [ ] Code refactored
- [ ] Tests bleiben grün (REFACTOR)

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

