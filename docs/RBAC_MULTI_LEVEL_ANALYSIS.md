# 🔍 RBAC: Multi-Level Interest Group Support

## Problemstellung

### Aktuelle Situation

Ein User kann mehrere Interest Groups (IG) mit **unterschiedlichen Berechtigungsleveln** haben:

**Beispiel:**
```
User: max.mustermann@company.com
├── Produktion (Level 3 - Abteilungsleiter)
└── Service (Level 2 - Teamleiter)
```

**Aktuelle Implementierung:**
- `get_user_level()` gibt nur das **höchste Level** zurück (hier: Level 3)
- `get_user_interest_groups()` gibt nur die **IDs** zurück, nicht die Levels pro IG
- **Problem**: User wird global als Level 3 behandelt, auch wenn er in Service nur Level 2 ist

**Konsequenzen:**
- ✅ Navigation: Korrekt (höchstes Level für Upload, etc.)
- ❌ Dokumenten-Liste: Sieht alle Dokumente aus beiden IGs, unabhängig vom IG-Level
- ❌ Kanban: Kann für **alle** Dokumente Kanban sehen (auch Service), obwohl er dort nur Level 2 ist
- ❌ Workflow: Kann für Service-Dokumente auch approve/reject (Level 4), obwohl er dort nur Level 2 ist

## Lösungskonzept

### 1. **UI-Anzeige** (Frontend)

Unter dem Level-Badge in der Navigation anzeigen:

```
Level 3 (Höchstes)
├── Produktion: Level 3
└── Service: Level 2
```

**Optionen:**
- A) Tooltip/Popover beim Hover über "Level 3"
- B) Erweiterte Anzeige mit Expand/Collapse
- C) Kompakte Anzeige: "Level 3 (Produktion: 3, Service: 2)"

**Empfehlung:** Option C (kompakt) + Option A (Details im Tooltip)

### 2. **Berechtigungslogik** (Backend + Frontend)

#### 2.1. Global vs. Context-Specific

| Feature | Basis | Logik |
|---------|-------|-------|
| **Navigation** | Global (höchstes Level) | `get_user_level()` |
| **Upload** | Global (höchstes Level) | `get_user_level() >= 4` |
| **Dokumenten-Liste** | Context (IG-Level) | `get_user_interest_groups()` für Filterung |
| **Kanban Sichtbarkeit** | Context (IG-Level) | IG-Level >= 3 für Dokument-IG |
| **Workflow-Transitions** | Context (IG-Level) | IG-Level >= required_level für Dokument-IG |
| **RAG Chat** | Context (IG-Level) | `get_user_interest_groups()` für Filterung |

#### 2.2. Neue Backend-Methode

```python
def get_user_interest_groups_with_levels(self, user_id: int) -> List[Dict[str, Any]]:
    """
    Hole Interest Groups mit deren Approval Levels.
    
    Returns:
        [
            {"interest_group_id": 1, "approval_level": 3, "interest_group_name": "Produktion"},
            {"interest_group_id": 2, "approval_level": 2, "interest_group_name": "Service"}
        ]
    """
```

#### 2.3. Context-Specific Permission Check

Für dokumentenbasierte Features (Kanban, Workflow):

```python
def can_perform_action_on_document(
    self,
    user_id: int,
    document_id: int,
    action: str,  # "view_kanban", "change_status", etc.
    required_level: int
) -> bool:
    """
    Prüfe ob User Aktion für spezifisches Dokument ausführen darf.
    
    Logik:
    1. Hole höchstes Level (global)
    2. Hole IG-Level des Dokuments
    3. Prüfe ob User dieses IG-Level hat >= required_level
    """
```

## Implementierungsplan

### Phase 1: Backend-Erweiterung

1. **Neue Methode:** `get_user_interest_groups_with_levels()`
   - Gibt Liste mit `{interest_group_id, approval_level, interest_group_name}` zurück
   - Nur aktive Memberships
   - Sortiert nach Level (höchstes zuerst)

2. **JWT Token erweitern:**
   - Aktuell: `interest_group_ids: [1, 2]`
   - Neu: `interest_groups_with_levels: [{id: 1, level: 3, name: "Produktion"}, {id: 2, level: 2, name: "Service"}]`

3. **Context-Specific Permission Check:**
   - `can_perform_action_on_document()` implementieren
   - Prüft IG-Level des Dokuments vs. User-IG-Level

### Phase 2: Frontend-Erweiterung

1. **UserContext erweitern:**
   - `interestGroupsWithLevels: Array<{id: number, level: number, name: string}>`
   - Helper: `getLevelForInterestGroup(igId: number): number`

2. **Navigation erweitern:**
   - Zeige IG + Levels unter Level-Badge
   - Tooltip mit Details

3. **Document-Specific Checks:**
   - Kanban: Prüfe IG-Level des Dokuments
   - Workflow: Prüfe IG-Level des Dokuments

### Phase 3: Testing

1. **Test-User erstellen:**
   - User mit Level 3 (Produktion) + Level 2 (Service)
   - Dokumente in beiden IGs erstellen

2. **Tests:**
   - Navigation zeigt korrektes höchstes Level
   - Dokumenten-Liste filtert korrekt
   - Kanban nur für Produktion sichtbar (Level 3), nicht für Service (Level 2)
   - Workflow: Kann nur für Produktion approve (Level 3 → 4 fehlt für Service)

## Offene Fragen

1. **Was passiert wenn User mehrere IGs hat, aber Dokument zu keiner IG gehört?**
   - Aktuell: User sieht Dokument nicht (Filter)
   - Vorschlag: Unverändert (Filter bleibt)

2. **Was passiert wenn Dokument zu mehreren IGs gehört?**
   - Aktuell: User sieht Dokument wenn er mindestens eine IG hat
   - Vorschlag: User-Level = Höchstes Level der gemeinsamen IGs

3. **Kann ein User Level 3 für IG-A haben und Level 4 für IG-B?**
   - Aktuell: Nein, Level 4 ist QM (global)
   - Vorschlag: Level 4 bleibt global (QM ist systemweit), aber IG-spezifische Level können 1-3 sein

## Empfehlung

**Kurzfristig (MVP):**
- ✅ UI-Anzeige der IG + Levels (nur Informationszweck)
- ✅ Global höchstes Level für Navigation/Upload
- ⚠️ Context-specific Checks für Kanban/Workflow (optional, später)

**Langfristig:**
- ✅ Vollständige context-specific Berechtigungen
- ✅ Document-IG-Level wird bei Workflow-Transitions geprüft
- ✅ Fehlermeldungen wenn User Aktion nicht ausführen darf (IG-Level zu niedrig)

