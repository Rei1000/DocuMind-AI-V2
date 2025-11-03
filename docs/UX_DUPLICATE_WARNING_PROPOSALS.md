# UX-Vorschläge: Duplikat-Warnung im Frontend

## 🎯 Problem

Aktuell wird die Duplikat-Warnung zwar im Backend erkannt, aber im Frontend nicht prominent genug angezeigt. Der User sieht nur eine kurze Success-Message und erfährt nicht, dass es bereits eine identische Datei gibt.

## 📊 Vorschläge für UX-Verbesserung

### **Option 1: Warning-Modal nach Upload (EMPFOHLEN)**

Nach erfolgreichem Upload wird ein Modal angezeigt, wenn ein Duplikat erkannt wurde:

```
┌─────────────────────────────────────────────────────┐
│  ⚠️  Duplikat erkannt                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Dieses Dokument ist bereits im System vorhanden! │
│                                                     │
│  Original-Dokument:                                │
│  📄 PA 7.3 [00] 240516 - Entwicklung...           │
│  ID: #6 | Hochgeladen: 3. Nov 2025                │
│                                                     │
│  ⚡ Aktion wählen:                                  │
│                                                     │
│  [📋 Zum Original springen] [✅ Als Duplikat      │
│                              behalten]             │
│                                                     │
│  Hinweis: Das Duplikat wurde gespeichert, aber    │
│  zeigt auf das Original-Dokument (ID 6).          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ User sieht sofort, dass ein Duplikat erkannt wurde
- ✅ Kann direkt zum Original springen
- ✅ Klare Information über die Situation

**Implementierung:**
- Modal öffnen wenn `uploadResponse.document.is_duplicate === true`
- Link zum Original: `/documents/${duplicate_of_document_id}`
- Option: "Als Duplikat behalten" oder "Löschen und zum Original"

---

### **Option 2: Warning-Banner in Success-Message**

Success-Message mit Warning-Banner kombinieren:

```
┌─────────────────────────────────────────────────────┐
│  ✅ Dokument erfolgreich hochgeladen!               │
│                                                     │
│  ⚠️  Duplikat-Hinweis                              │
│  ┌───────────────────────────────────────────────┐ │
│  │ ⚠️  Dieses Dokument existiert bereits im       │ │
│  │     System (Dokument #6).                      │ │
│  │                                                 │ │
│  │     [📋 Zum Original springen]                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  (3 Seiten generiert)                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ User sieht Success + Warning gleichzeitig
- ✅ Nicht zu aufdringlich

---

### **Option 3: Duplikat-Badge in Dokument-Detail-Ansicht**

In der Dokument-Detail-Seite ein sichtbares Badge hinzufügen:

```
┌─────────────────────────────────────────────────────┐
│  PA 7.3 [00] 240516 - Entwicklung...               │
│                                                     │
│  📋 Document Information                            │
│  ┌─────────────────────────────────────────────┐  │
│  │ ⚠️  DUPLIKAT                                  │  │
│  │ Dieses Dokument ist eine Kopie von #6        │  │
│  │ [Zum Original →]                             │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Dokumenttyp: Flussdiagramm                         │
│  Workflow-Status: 📝 Entwurf                        │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Immer sichtbar beim Betrachten des Dokuments
- ✅ User kann später noch zum Original springen
- ✅ Klare Kennzeichnung

---

### **Option 4: Duplikat-Icon in Dokumenten-Liste**

In der Dokumenten-Tabelle/Liste ein Icon hinzufügen:

```
┌─────────────────────────────────────────────────────┐
│  Dokumente                                          │
│                                                     │
│  ┌─────┬─────────────────────────────────────┐   │
│  │ ID  │ Dateiname              │ Status │ ⚠️ │   │
│  ├─────┼─────────────────────────────────────┤   │
│  │  6  │ PA 7.3 [00]...         │ Draft  │   │   │
│  │  9  │ PA 7.3 [00]...         │ Draft  │ ⚠️ │   │
│  │  7  │ PA 8.2.1...            │ Appr. │   │   │
│  └─────┴─────────────────────────────────────┘   │
│                                                     │
│  ⚠️ = Duplikat (zeigt auf Original)                │
└─────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Schnelle Übersicht in der Liste
- ✅ User sieht Duplikate auf einen Blick

---

### **Option 5: Kombiniert (Option 1 + 3 + 4) - BESTE UX**

Alle oben genannten Optionen kombinieren:

1. **Nach Upload:** Warning-Modal (Option 1)
2. **In Dokument-Detail:** Warning-Banner oben (Option 3)
3. **In Dokumenten-Liste:** Duplikat-Icon (Option 4)

**Vorteile:**
- ✅ Maximale Sichtbarkeit
- ✅ User wird an mehreren Stellen informiert
- ✅ Beste User Experience

---

## 🎨 Design-Details

### **Farben & Icons:**

```tsx
// Warning-Banner (gelb/orange)
<div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
  <div className="flex items-start">
    <span className="text-yellow-400 text-xl mr-3">⚠️</span>
    <div className="flex-1">
      <h3 className="text-yellow-800 font-semibold">Duplikat erkannt</h3>
      <p className="text-yellow-700 text-sm mt-1">
        Dieses Dokument existiert bereits im System.
      </p>
      <a href={`/documents/${duplicate_of_document_id}`} 
         className="text-yellow-800 underline mt-2 inline-block">
        Zum Original springen →
      </a>
    </div>
  </div>
</div>

// Badge (orange/warnend)
<span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800 border border-orange-300">
  <span>⚠️</span>
  <span>DUPLIKAT</span>
</span>

// Icon in Liste (klein, aber sichtbar)
{is_duplicate && (
  <span className="text-orange-500 text-lg" title="Duplikat - zeigt auf Dokument #X">
    ⚠️
  </span>
)}
```

---

## 🚀 Empfohlene Implementierung

**Phase 1 (Quick Win):**
- ✅ Option 2: Warning-Banner in Success-Message (einfach, schnell)
- ✅ Option 3: Badge in Dokument-Detail (wichtig für spätere Betrachtung)

**Phase 2 (Optimiert):**
- ✅ Option 1: Warning-Modal (beste UX, etwas aufwendiger)
- ✅ Option 4: Icon in Liste (für Übersicht)

---

## 📝 Technische Details

### **API Response Struktur:**

```typescript
interface UploadDocumentResponse {
  success: boolean
  message: string  // "⚠️ Warning: Duplicate document detected!..."
  document: {
    id: number
    is_duplicate: boolean
    duplicate_of_document_id: number | null
    // ... andere Felder
  }
}
```

### **Frontend States:**

```typescript
const [isDuplicate, setIsDuplicate] = useState(false)
const [duplicateOfDocumentId, setDuplicateOfDocumentId] = useState<number | null>(null)
const [showDuplicateModal, setShowDuplicateModal] = useState(false)
```

---

## ✅ Nächste Schritte

1. **Welche Option bevorzugst du?** (Ich empfehle Option 5: Kombiniert)
2. **Soll ich direkt implementieren?** Oder erst Design-Mockups zeigen?
3. **Soll der Upload blockiert werden?** Oder nur Warnung anzeigen (wie aktuell)?

