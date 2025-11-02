# 🧪 RBAC Test-User Szenarien

> **Zweck:** Definition von Test-Usern für RBAC-Implementierung und Testing

---

## 📋 Test-User Übersicht

### **Level 5: QMS Admin**
```
User: qms.admin@company.com
- is_qms_admin: true
- Interest Groups: Alle (oder keine IG-Zuordnung nötig)
- Zweck: Vollzugriff-Tests, Benutzerverwaltung-Tests
```

### **Level 4: QM-Mitarbeiter**
```
User: qm.mitarbeiter@company.com
- approval_level: 4 (in einer IG)
- Interest Group: "Quality Management" (IG Code: qm)
- Zweck: Upload-Tests, Workflow-Freigabe-Tests, alle Dokumente sehen
```

### **Level 3: Abteilungsleiter**
```
User: abteilungsleiter.service@company.com
- approval_level: 3
- Interest Group: "Service" (IG Code: service)
- Zweck: Workflow Draft→Reviewed Tests (nur eigene IG), Kanban-Tests

User: abteilungsleiter.produktion@company.com
- approval_level: 3
- Interest Group: "Produktion" (IG Code: production)
- Zweck: Mehrere IG-Tests, Isolation zwischen IG-Gruppen
```

### **Level 2: Teamleiter**
```
User: teamleiter.service@company.com
- approval_level: 2
- Interest Group: "Service" (IG Code: service)
- Zweck: Tabellen-Ansicht Tests, Kommentar-Tests, kein Kanban

User: teamleiter.it@company.com
- approval_level: 2
- Interest Group: "IT" (IG Code: it)
- Zweck: Mehrere IG-Tests, RAG Chat IG-Filter Tests
```

### **Level 1: Mitarbeiter**
```
User: mitarbeiter.service@company.com
- approval_level: 1
- Interest Group: "Service" (IG Code: service)
- Zweck: RAG Chat Only Tests, minimale Navigation Tests

User: mitarbeiter.it@company.com
- approval_level: 1
- Interest Group: "IT" (IG Code: it)
- Zweck: RAG Chat IG-Filter Tests, Isolation Tests
```

---

## 🎯 Test-Szenarien pro User

### **qms.admin@company.com (Level 5)**
1. ✅ Navigation: Alle Links sichtbar (Benutzer, Upload, Dokumente, Prompt, AI Models)
2. ✅ Benutzerverwaltung: Vollzugriff
3. ✅ Dokument Upload: Erfolgreich
4. ✅ Dokumenten-Workflow: Alle Dokumente sehen, alle Status-Änderungen
5. ✅ RAG Chat: Alle Dokumente (keine IG-Filterung)
6. ✅ Prompt-Verwaltung: Vollzugriff
7. ✅ AI Models: Vollzugriff

### **qm.mitarbeiter@company.com (Level 4, IG: QM)**
1. ✅ Navigation: Kein "Benutzer", kein "Prompt", kein "AI Models"
2. ✅ Dokument Upload: Erfolgreich
3. ✅ Dokumenten-Workflow: Alle Dokumente sehen, Draft→Reviewed→Approved
4. ✅ RAG Chat: Alle Dokumente (keine IG-Filterung)
5. ❌ Benutzerverwaltung: Seite nicht erreichbar / ausgeblendet

### **abteilungsleiter.service@company.com (Level 3, IG: Service)**
1. ✅ Navigation: Kein "Upload", kein "Benutzer", kein "Prompt", kein "AI Models"
2. ✅ Dokumenten-Workflow: Nur Service-Dokumente sehen
3. ✅ Kanban: Sichtbar, aber nur Service-Dokumente
4. ✅ Workflow: Draft → Reviewed möglich (nur Service-Dokumente)
5. ❌ Workflow: Reviewed → Approved NICHT möglich
6. ✅ RAG Chat: Nur Service-Dokumente
7. ✅ Kommentare: Hinzufügen möglich

### **teamleiter.service@company.com (Level 2, IG: Service)**
1. ✅ Navigation: Kein "Upload", kein "Benutzer", kein Kanban-View
2. ✅ Dokumenten-Übersicht: Tabellen-Ansicht (kein Kanban)
3. ✅ Dokumenten-Detail: Lesen + Kommentieren
4. ❌ Workflow: Keine Status-Änderungen möglich
5. ✅ RAG Chat: Nur Service-Dokumente
6. ❌ Kanban: Nicht sichtbar

### **mitarbeiter.service@company.com (Level 1, IG: Service)**
1. ✅ Navigation: Nur "Home (RAG Chat)"
2. ✅ RAG Chat: Nur Service-Dokumente
3. ✅ Dokumenten-Detail: Über Link aus RAG Chat, schreibgeschützt
4. ❌ Dokumenten-Übersicht: Seite nicht erreichbar
5. ❌ Upload: Nicht möglich
6. ❌ Workflow: Nicht sichtbar

---

## 🔄 Multi-IG Szenarien

### **User mit mehreren Interest Groups:**
```
User: multi.ig.user@company.com
- Interest Group 1: "Service" (Level 2)
- Interest Group 2: "IT" (Level 3)
- Zweck: Testen welches Level verwendet wird (höchstes Level)
```

**Erwartetes Verhalten:**
- User Level = 3 (höchstes approval_level)
- Sehen Dokumente aus beiden IG (Service + IT)
- Workflow: Draft → Reviewed möglich (beide IG)
- Kein Approved/Rejected (nur Level 4+)

---

## 🎯 Test-Dokumente Setup

### **Dokumente für Tests:**
1. **Dokument A** - Interest Group: "Service" - Status: Draft
2. **Dokument B** - Interest Group: "Service" - Status: Reviewed
3. **Dokument C** - Interest Group: "IT" - Status: Draft
4. **Dokument D** - Interest Group: "Quality Management" - Status: Approved
5. **Dokument E** - Interest Groups: ["Service", "IT"] - Status: Draft

**Erwartete Sichtbarkeit:**
- **Level 1 (Service):** Nur Dokument A, B, E (in RAG Chat)
- **Level 2 (Service):** Dokument A, B, E (in Tabelle)
- **Level 3 (Service):** Dokument A, B, E (in Kanban, kann A & E nach Reviewed ziehen)
- **Level 4 (QM):** Alle Dokumente (A, B, C, D, E)
- **Level 5 (Admin):** Alle Dokumente (A, B, C, D, E)

---

## ✅ Checklist für Test-User Erstellung

- [ ] qms.admin@company.com (Level 5) - bereits vorhanden?
- [ ] qm.mitarbeiter@company.com (Level 4, IG: QM) - erstellen
- [ ] abteilungsleiter.service@company.com (Level 3, IG: Service) - erstellen
- [ ] abteilungsleiter.produktion@company.com (Level 3, IG: Produktion) - erstellen
- [ ] teamleiter.service@company.com (Level 2, IG: Service) - erstellen
- [ ] teamleiter.it@company.com (Level 2, IG: IT) - erstellen
- [ ] mitarbeiter.service@company.com (Level 1, IG: Service) - erstellen
- [ ] mitarbeiter.it@company.com (Level 1, IG: IT) - erstellen
- [ ] multi.ig.user@company.com (Level 2+3, IG: Service+IT) - erstellen

**Passwörter:** Alle: `123` (einfach für Tests)

