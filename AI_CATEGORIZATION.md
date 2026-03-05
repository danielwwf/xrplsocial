# AI Kategorisierung - Dokumentation

## Was wurde gemacht

### 1. AI-Kategorisierungen erstellt
- **207 Branches** wurden manuell über AI-Chat kategorisiert
- Ergebnis: `stats/data/ai_categories.json` (736 Zeilen)
- Jeder Branch hat: amendment, type, confidence, source

### 2. Frontend-Anpassungen in index.html

#### Neue Funktionen hinzugefügt:
```javascript
// Lädt AI-Kategorien aus JSON
async function loadAICategories() {
    const response = await fetch('data/ai_categories.json');
    aiCategories = await response.json();
}

// Gibt AI-Kategorie zurück (oder Fallback zu Keywords)
function getAICategory(branchName) {
    if (aiCategories && aiCategories[branchName]) {
        return aiCategories[branchName];
    }
    return keywordCategorize(branchName); // Fallback
}
```

#### Render-Funktion angepasst:
```javascript
function renderAmendments() {
    // Statt: const category = getCategory(b.name);
    // Jetzt: const aiCat = getAICategory(b.name);
    //        const category = aiCat?.amendment || 'Other';
}
```

### 3. Datenstruktur

**Beispiel aus ai_categories.json:**
```json
{
  "ximinez/lending-sendmulti": {
    "amendment": "Lending",
    "type": "Feature",
    "confidence": 0.9,
    "source": "ai_kimi"
  }
}
```

### 4. Kategorien-Übersicht

| Amendment | Anzahl |
|-----------|--------|
| Other | 76 |
| Testing & CI | 35 |
| OpenTelemetry | 10 |
| Lending | 13 |
| Code Modularization | 7 |
| Rust/WASM | 5 |
| Confidential Transfers | 2 |
| Smart Escrow | 2 |
| Batch Transactions | 1 |

### 5. Workflow-Verhalten

**Vorher:**
- Cache wurde bei jedem Run gelöscht
- Alle Branches mussten neu analysiert werden

**Nachher:**
- Cache bleibt erhalten
- Nur neue/geänderte Branches werden analysiert
- AI-Daten werden aus `ai_categories.json` geladen

### 6. Dateien

**Wichtige Dateien:**
- `stats/data/ai_categories.json` - Die 207 AI-Kategorisierungen
- `stats/data/branches.json` - Branch-Daten mit Commits
- `stats/index.html` - Frontend mit AI-Anzeige

**Skripte:**
- `scripts/ai_categorize.py` - AI-Kategorisierungs-Logik
- `scripts/integrate_categories.py` - Integration in branches.json

## Nutzung

Die AI-Kategorien werden automatisch geladen wenn die Seite geöffnet wird:

1. `loadData()` ruft `loadAICategories()` auf
2. `renderAmendments()` nutzt `getAICategory()` für jeden Branch
3. Anzeige gruppiert nach AI-Kategorien (nicht mehr nur Keywords)

## Wartung

Wenn neue Branches hinzukommen:
1. Workflow lädt existierende Kategorien aus Cache
2. Neue Branches werden mit AI/Keywords kategorisiert
3. Ergebnis wird in `ai_categories.json` gespeichert

## Kosten

- Einmalig: ~$0.24 für 207 AI-Calls (überlastete API)
- Danach: $0 (Cache-basiert)
