# DocuMind-AI Design System - Exakte Spezifikationen

**Ziel:** Eliminierung von Design-"Unruhe" beim Seitenwechsel durch 100% konsistente Komponenten.

## 🎯 Problem-Analyse

### Aktuelle Inkonsistenzen:
1. **Sidebars**: Unterschiedliche Breiten, Padding, Shadows
2. **Cards**: Verschiedene Border-Stärken, Shadows, Padding-Werte
3. **Filter-Panels**: Jede Seite hat eigene Filter-Styles
4. **Spacing**: Inkonsistente Abstände zwischen Elementen
5. **Headers**: Unterschiedliche Padding-Werte und Styles

### User-Feedback:
> "Es kommt Unruhe auf beim Wechseln zwischen Seiten, weil sich Größen und Styles ändern."

---

## 📐 Design-System Standards

### 1. **Sidebar-Container** (SessionSidebar, FilterPanel, DocumentTypes Panel)

**Standard:**
```tsx
className="flex flex-col h-full bg-white rounded-lg shadow-md border border-gray-200"
```

**Spezifikation:**
- **Breite**: `w-[320px]` (fest, kein `w-[300px]` oder `w-[350px]` mehr!)
- **Hintergrund**: `bg-white`
- **Border**: `border border-gray-200` (1px)
- **Shadow**: `shadow-md` (nicht `shadow-lg`, nicht `shadow-sm`!)
- **Border Radius**: `rounded-lg` (8px)

**Header (immer gleich):**
```tsx
className="p-4 border-b border-gray-200"
```
- **Padding**: `p-4` (16px) - NIEMALS `p-6` oder `p-3`!
- **Border**: `border-b border-gray-200`

**Content Area:**
```tsx
className="flex-1 overflow-y-auto p-4"
```
- **Padding**: `p-4` (16px) - konsistent!

**Footer (wenn vorhanden):**
```tsx
className="p-4 border-t border-gray-200"
```

---

### 2. **Card-Komponenten** (Standard für alle Inhalts-Karten)

**Es gibt 3 Varianten:**

#### **Card SM** (Kleine Cards, z.B. in Listen)
```tsx
<Card padding="sm" shadow="sm">
```
- **Padding**: `p-4` (16px)
- **Shadow**: `shadow-sm`
- **Border**: `border border-gray-200`

#### **Card MD** (Standard, z.B. Dokumenten-Cards)
```tsx
<Card padding="md" shadow="sm">
```
- **Padding**: `p-6` (24px)
- **Shadow**: `shadow-sm`
- **Border**: `border border-gray-200`

#### **Card LG** (Große Cards, z.B. Detail-Ansichten)
```tsx
<Card padding="lg" shadow="sm">
```
- **Padding**: `p-8` (32px)
- **Shadow**: `shadow-sm`
- **Border**: `border border-gray-200`

**WICHTIG:** 
- **NIEMALS** `shadow-lg` für Cards!
- **NIEMALS** manuelle `bg-white rounded-lg border` statt Card-Komponente!
- **NIEMALS** verschiedene Padding-Werte wie `p-12`!

**Verwendung:**
```tsx
import Card from '@/components/ui/Card'

// ✅ RICHTIG
<Card padding="md">Inhalt</Card>

// ❌ FALSCH
<div className="bg-white rounded-lg border border-gray-200 p-6">Inhalt</div>
```

---

### 3. **Filter-Panel Komponente** (Standardisiert für ALLE Filter)

**Ziel:** Alle Filter-Panels (Dashboard, Documents, etc.) nutzen die gleiche Komponente.

**Standard-FilterPanel:**
- Nutzt die Sidebar-Spezifikation (s.o.)
- Header mit Titel + Toggle-Button
- Content mit konsistenten Input-Styles
- Footer mit Action-Buttons

**Input-Felder (Standard):**
```tsx
className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg 
          focus:ring-2 focus:ring-blue-500 focus:border-transparent"
```

**Select-Felder:**
```tsx
className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg 
          focus:ring-2 focus:ring-blue-500 focus:border-transparent"
```

**Labels:**
```tsx
className="block text-sm font-medium text-gray-700 mb-2"
```

---

### 4. **Spacing-System** (Konsistente Abstände)

**Abstände zwischen großen Elementen:**
- `space-y-6` oder `gap-6` (24px) - Standard
- `space-y-4` oder `gap-4` (16px) - Kompakt
- `space-y-8` oder `gap-8` (32px) - Großzügig

**Innerhalb von Cards:**
- `space-y-4` (16px) - Standard
- `space-y-3` (12px) - Kompakt
- `space-y-6` (24px) - Großzügig

**Zwischen Filter-Gruppen:**
- `space-y-4` (16px) - Standard

---

### 5. **Header-Standard** (Page-Headers)

**Standard-Header:**
```tsx
<div className="mb-8">
  <h1 className="text-3xl font-bold text-gray-900 mb-2">
    Seitentitel
  </h1>
  <p className="text-gray-600">
    Beschreibung
  </p>
</div>
```

**Spezifikation:**
- **Margin Bottom**: `mb-8` (32px) - NIEMALS `mb-6`!
- **H1**: `text-3xl font-bold text-gray-900 mb-2`
- **Description**: `text-gray-600`

---

### 6. **Layout-Container** (Standard für alle Seiten)

**Main Container:**
```tsx
<div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
```

**Spezifikation:**
- **Max Width**: `max-w-[1800px]`
- **Padding X**: `px-4 sm:px-6 lg:px-8`
- **Padding Y**: `py-8` (32px)

---

### 7. **Button-Standard** (bereits implementiert)

**Verwendung:**
```tsx
import { Button } from '@/components/ui'

<Button variant="primary" loading={isLoading}>
  Text
</Button>
```

**NIEMALS** manuelle Button-Styles!

---

## 🔧 Implementation Plan

### Phase 1: Sidebar-Standardisierung
- [ ] Alle Sidebars auf `w-[320px]` setzen
- [ ] Shadow auf `shadow-md` vereinheitlichen
- [ ] Padding auf `p-4` vereinheitlichen
- [ ] Border `border-gray-200` konsistent

### Phase 2: Card-Standardisierung
- [ ] Alle manuellen `bg-white rounded-lg border` durch `Card`-Komponente ersetzen
- [ ] Padding-Varianten (sm/md/lg) konsequent nutzen
- [ ] Shadow auf `shadow-sm` für alle Cards
- [ ] Keine `p-12` oder andere inkonsistente Werte mehr!

### Phase 3: Filter-Standardisierung
- [ ] FilterPanel-Komponente als Standard definieren
- [ ] Dokumenten-Seite: Filter oben durch Sidebar ersetzen ODER Filter-Styles angleichen
- [ ] Prompt-Management: Filter-Standard anwenden

### Phase 4: Spacing-Standardisierung
- [ ] Alle `mb-6` auf `mb-8` für Page-Headers
- [ ] Abstände zwischen Cards: `gap-6` oder `space-y-6`
- [ ] Innerhalb Cards: `space-y-4`

### Phase 5: Final Check
- [ ] Alle Seiten durchgehen
- [ ] Browser-Test: Seitenwechsel auf "Unruhe" prüfen
- [ ] Alle Cards sollten gleich aussehen
- [ ] Alle Filter sollten gleich aussehen
- [ ] Alle Sidebars sollten gleich aussehen

---

## ✅ Success Criteria

**Beim Seitenwechsel:**
1. ✅ Sidebar-Breiten bleiben gleich (320px)
2. ✅ Card-Styles bleiben gleich (padding, shadow, border)
3. ✅ Filter-Panels sehen gleich aus
4. ✅ Spacing bleibt konsistent
5. ✅ Keine "springenden" Elemente mehr!

---

## 📚 Notion/Linear Inspiration

**Notion-Style:**
- Subtile Borders (`border-gray-200`)
- Sanfte Shadows (`shadow-sm`)
- Konsistente Padding (`p-4`, `p-6`)
- Einheitliche Sidebar-Breiten
- Filter-Panels immer links oder oben, gleicher Style

**Linear-Style:**
- Minimalistische Cards
- Konsistente Spacing
- Einheitliche Input-Styles
- Keine "Design-Sprünge" beim Navigieren

---

## 🎨 Farb-System (bereits definiert)

- **Primary**: `#2B6399` (Logo Blue)
- **Text**: `text-gray-900` (Headings), `text-gray-600` (Body)
- **Border**: `border-gray-200`
- **Background Cards**: `bg-white`
- **Background Page**: Gradient (`from-blue-50 via-white to-gray-50`)

---

**Status:** 📋 Plan erstellt - Ready for Implementation
