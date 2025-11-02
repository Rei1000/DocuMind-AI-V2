# 🚀 RBAC Multi-Level: Vollständige Implementierung

## Ziel

1. **UI-Anzeige**: Interest Groups + Levels in Navigation
2. **Context-Specific Checks**: Dokument-Aktionen basierend auf IG-Level prüfen

## Architektur-Überblick

```
User (mitarbeiter@company.com)
├── Produktion: Level 3
└── Service: Level 2

Dokument A (zu Produktion zugeordnet)
└── User kann: Kanban sehen, Draft→Reviewed (Level 3 ✅)

Dokument B (zu Service zugeordnet)  
└── User kann: Kein Kanban (Level 2 ❌), nur Tabelle
```

## Implementierungsplan

### Phase 1: Backend - IG mit Levels

#### 1.1 Neue Methode: `get_user_interest_groups_with_levels()`

```python
# contexts/documentupload/infrastructure/permission_service.py

def get_user_interest_groups_with_levels(self, user_id: int) -> List[Dict[str, Any]]:
    """
    Hole Interest Groups mit deren Approval Levels.
    
    Returns:
        [
            {
                "interest_group_id": 1,
                "approval_level": 3,
                "interest_group_name": "Produktion"
            },
            {
                "interest_group_id": 2,
                "approval_level": 2,
                "interest_group_name": "Service"
            }
        ]
        Oder leere Liste [] für Level 4-5 (alle IG)
    """
    from backend.app.models import InterestGroup
    
    user_level = self.get_user_level(user_id)
    
    # Level 4+ (QM, QMS Admin): Alle IG (keine Filterung)
    if user_level >= 4:
        return []  # Leere Liste = alle IG
    
    # Level 1-3: Nur eigene Interest Groups aus aktiven Memberships
    memberships = (
        self.db.query(UserGroupMembership, InterestGroup)
        .join(InterestGroup, UserGroupMembership.interest_group_id == InterestGroup.id)
        .filter(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.is_active == True
        )
        .order_by(UserGroupMembership.approval_level.desc())
        .all()
    )
    
    return [
        {
            "interest_group_id": m.interest_group_id,
            "approval_level": m.approval_level,
            "interest_group_name": ig.name
        }
        for m, ig in memberships
    ]
```

#### 1.2 Context-Specific Permission Check

```python
# contexts/documentupload/infrastructure/permission_service.py

def can_perform_action_on_document(
    self,
    user_id: int,
    document_interest_group_ids: List[int],
    action: str,  # "view_kanban", "change_status_draft_to_reviewed", etc.
    required_level: int
) -> bool:
    """
    Prüfe ob User Aktion für Dokument mit bestimmten IGs ausführen darf.
    
    Logik:
    - Level 4-5: Immer True (Vollzugriff)
    - Level 1-3: Prüfe ob User mindestens eine IG des Dokuments mit Level >= required_level hat
    
    Beispiel:
        User: Level 3 (Produktion), Level 2 (Service)
        Dokument: Produktion (IG-ID: 1)
        Aktion: view_kanban (required_level: 3)
        → True (User hat Level 3 für Produktion)
        
        User: Level 3 (Produktion), Level 2 (Service)
        Dokument: Service (IG-ID: 2)
        Aktion: view_kanban (required_level: 3)
        → False (User hat nur Level 2 für Service)
    
    Args:
        user_id: User ID
        document_interest_group_ids: Interest Groups des Dokuments
        action: Aktion (zur Dokumentation)
        required_level: Benötigtes Level für Aktion
        
    Returns:
        True wenn berechtigt, False sonst
    """
    user_level = self.get_user_level(user_id)
    
    # Level 4+ (QM, QMS Admin): Immer berechtigt
    if user_level >= 4:
        return True
    
    # Level 1-3: Prüfe IG-Level
    user_igs_with_levels = self.get_user_interest_groups_with_levels(user_id)
    
    # Erstelle Mapping: IG-ID → Level
    user_ig_level_map = {
        ig["interest_group_id"]: ig["approval_level"]
        for ig in user_igs_with_levels
    }
    
    # Prüfe ob User für mindestens eine IG des Dokuments das required_level hat
    for doc_ig_id in document_interest_group_ids:
        user_level_for_ig = user_ig_level_map.get(doc_ig_id, 0)
        if user_level_for_ig >= required_level:
            return True
    
    # User hat für keine IG des Dokuments das required_level
    return False
```

#### 1.3 JWT Token erweitern

```python
# contexts/accesscontrol/application/auth_login_service.py

def _create_token_data(self, user: User) -> Dict[str, Any]:
    # ... existing code ...
    
    if self.permission_service:
        try:
            # ... existing code (user_level, is_qms_admin, interest_group_ids) ...
            
            # NEU: Interest Groups mit Levels
            interest_groups_with_levels = self.permission_service.get_user_interest_groups_with_levels(user.id)
            token_data["interest_groups_with_levels"] = interest_groups_with_levels
            
        except Exception as e:
            # ... fallback ...
            token_data["interest_groups_with_levels"] = []
```

### Phase 2: Frontend - UI-Anzeige

#### 2.1 UserContext erweitern

```typescript
// frontend/lib/contexts/UserContext.tsx

export interface UserContextType {
  // ... existing fields ...
  interestGroupsWithLevels: Array<{
    id: number
    level: number
    name: string
  }>
  // Helper Functions
  getLevelForInterestGroup: (igId: number) => number
  canPerformActionOnDocument: (
    documentInterestGroupIds: number[],
    requiredLevel: number
  ) => boolean
}
```

#### 2.2 Navigation erweitern

```typescript
// frontend/app/components/Navigation.tsx

const { userLevel, interestGroupsWithLevels } = useUser()

// Format: "Level 3 (Produktion: 3, Service: 2)"
const levelDisplay = interestGroupsWithLevels.length > 0
  ? `Level ${userLevel} (${interestGroupsWithLevels
      .sort((a, b) => b.level - a.level) // Höchstes Level zuerst
      .map(ig => `${ig.name}: ${ig.level}`)
      .join(', ')})`
  : `Level ${userLevel}`

// In JSX:
<span className="ml-1 text-gray-500">{levelDisplay}</span>
```

### Phase 3: Context-Specific Checks im Frontend

#### 3.1 Kanban Sichtbarkeit

```typescript
// frontend/app/documents/page.tsx

const canViewKanban = useMemo(() => {
  // Level 4-5: Immer Kanban
  if (userLevel >= 4) return true
  
  // Level 1-2: Kein Kanban
  if (userLevel < 3) return false
  
  // Level 3: Nur wenn Dokument zu IG mit Level >= 3 gehört
  // → Wird pro Dokument geprüft (siehe unten)
  return true
}, [userLevel])

// In Kanban-Ansicht: Dokumente filtern
const visibleDocuments = documents.filter(doc => {
  // Level 4-5: Alle Dokumente
  if (userLevel >= 4) return true
  
  // Level 1-2: Nur Dokumente aus eigenen IGs (bereits gefiltert durch Backend)
  if (userLevel < 3) return true
  
  // Level 3: Nur Dokumente, für die User Level >= 3 hat
  return canPerformActionOnDocument(doc.interest_group_ids, 3)
})
```

#### 3.2 Workflow Transitions

```typescript
// frontend/app/documents/page.tsx

const canChangeStatus = useMemo(() => {
  return (document: WorkflowDocument, toStatus: string) => {
    const requiredLevel = getRequiredLevelForTransition(
      document.workflow_status,
      toStatus
    )
    
    // Level 4-5: Immer erlaubt
    if (userLevel >= 4) return true
    
    // Prüfe IG-Level des Dokuments
    return canPerformActionOnDocument(
      document.interest_group_ids,
      requiredLevel
    )
  }
}, [userLevel, canPerformActionOnDocument])
```

### Phase 4: Backend Integration

#### 4.1 Dokumenten-Liste: IG-Level Info

```python
# contexts/documentupload/interface/router.py

@router.get("/", response_model=GetUploadsListResponse)
async def get_uploads_list(...):
    # ... existing code ...
    
    # NEU: Für jedes Dokument die IG-Level-Info hinzufügen
    # (optional, falls Frontend braucht)
```

#### 4.2 Workflow-Status-Änderung: Context-Specific Check

```python
# contexts/documentupload/interface/router.py

@router.patch("/{document_id}/workflow-status")
async def change_workflow_status(...):
    # ... existing code ...
    
    # NEU: Context-specific Permission Check
    document_ig_ids = [ig.interest_group_id for ig in document.interest_groups]
    required_level = get_required_level_for_transition(from_status, to_status)
    
    can_perform = permission_service.can_perform_action_on_document(
        user_id=current_user_id,
        document_interest_group_ids=document_ig_ids,
        action=f"change_status_{from_status}_to_{to_status}",
        required_level=required_level
    )
    
    if not can_perform:
        raise HTTPException(
            status_code=403,
            detail=f"Keine Berechtigung für Status-Änderung. Benötigt Level {required_level} für Interest Group(s) des Dokuments."
        )
```

## Testing

### Test-User Setup

```
User: max.mustermann@company.com
├── Produktion (Level 3)
└── Service (Level 2)
```

### Test-Szenarien

1. **Kanban Sichtbarkeit**
   - ✅ Dokument (Produktion) → Kanban sichtbar
   - ❌ Dokument (Service) → Kein Kanban, nur Tabelle

2. **Workflow Transitions**
   - ✅ Draft → Reviewed für Produktion (Level 3)
   - ❌ Draft → Reviewed für Service (Level 2 < 3)

3. **Dokumenten-Liste**
   - ✅ Zeigt Dokumente aus beiden IGs
   - ✅ Filtert korrekt nach IG-Level

## Migration

### Schrittweise Einführung

1. **Step 1**: Backend-Methoden implementieren (Phase 1)
2. **Step 2**: UI-Anzeige (Phase 2) - nur Informationszweck
3. **Step 3**: Context-specific Checks (Phase 3-4) - funktionale Änderungen

### Rückwärtskompatibilität

- JWT Token: `interest_group_ids` bleibt erhalten (Fallback)
- Frontend: Graceful Degradation wenn `interest_groups_with_levels` fehlt
- Backend: Legacy-Checks bleiben als Fallback

