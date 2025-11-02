# 📋 RBAC: UI-Anzeige für Interest Groups & Levels

## Vorschlag: UI-Anzeige in Navigation

### Option A: Kompakt (Empfehlung)
```
mitarbeiter@company.com • Level 3 (Produktion: 3, Service: 2) • Online
```

### Option B: Mit Tooltip/Popover
```
mitarbeiter@company.com • Level 3 • Online
                              ↑
                        Hover zeigt:
                        ├── Produktion: Level 3
                        └── Service: Level 2
```

### Option C: Expand/Collapse
```
mitarbeiter@company.com • Level 3 ▼ • Online
                        ├── Produktion: Level 3
                        └── Service: Level 2
```

**Empfehlung:** Option A (kompakt) für MVP, später Option B (Tooltip) für Details

## Implementierung

### 1. Backend: Neue Methode

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
    """
    from backend.app.models import InterestGroup
    
    user_level = self.get_user_level(user_id)
    
    # Level 4+ (QM, QMS Admin): Alle IG (keine Filterung)
    if user_level >= 4:
        return []  # Leere Liste = alle IG
    
    # Level 1-3: Nur eigene Interest Groups
    memberships = (
        self.db.query(UserGroupMembership, InterestGroup)
        .join(InterestGroup, UserGroupMembership.interest_group_id == InterestGroup.id)
        .filter(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.is_active == True
        )
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

### 2. JWT Token erweitern

```python
# contexts/accesscontrol/application/auth_login_service.py

def _create_token_data(self, user: User) -> Dict[str, Any]:
    # ... existing code ...
    
    if self.permission_service:
        try:
            # ... existing code ...
            
            # NEU: Interest Groups mit Levels
            interest_groups_with_levels = self.permission_service.get_user_interest_groups_with_levels(user.id)
            token_data["interest_groups_with_levels"] = interest_groups_with_levels
            
        except Exception as e:
            # ... fallback ...
```

### 3. Frontend: UserContext erweitern

```typescript
// frontend/lib/contexts/UserContext.tsx

export interface UserContextType {
  // ... existing fields ...
  interestGroupsWithLevels: Array<{
    id: number
    level: number
    name: string
  }>
}

// In parseJWTToken():
const interest_groups_with_levels = payload.interest_groups_with_levels || []
setInterestGroupsWithLevels(interest_groups_with_levels)
```

### 4. Frontend: Navigation erweitern

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

