"""
JSON-Schema-Extraktion aus Standard Prompts.

Extrahiert JSON-Struktur-Informationen aus Standard Prompts (prompt_templates),
um daraus optimierte Custom RAG Chat Prompts zu generieren.

CR-P2.2: Auto-Custom-Prompt-Generierung

Dieses Modul stellt Funktionen zur Verfügung, die:
1. JSON-Schema-Abschnitte in Standard Prompts lokalisieren
2. JSON-Strukturen extrahieren und parsen
3. Top-Level-Keys und verschachtelte Strukturen identifizieren
4. Strukturierte Beschreibungen für Custom-Prompt-Generierung erstellen

Author: AI Assistant
Version: 2.7.3
Stand: 2025-11-17
"""

import json
import re
from typing import Optional, Tuple, Dict, Any, List


def locate_json_schema(prompt_text: str) -> Optional[Tuple[int, int]]:
    """
    Findet den Start- und End-Index des JSON-Schema-Abschnitts im Prompt.
    
    Sucht nach Schema-Markern wie:
    - "JSON-Struktur"
    - "Ausgabeformat"
    - "JSON-Ausgabeformat"
    - "```json"
    - "🧩 JSON"
    
    Die Funktion identifiziert den Beginn des JSON-Schema-Abschnitts durch
    Erkennung von Markern und bestimmt das Ende durch Code-Block-Marker (```)
    oder durch Analyse der JSON-Struktur (schließende Klammern).
    
    Args:
        prompt_text: Der zu analysierende Prompt-Text. Kann None oder leer sein.
        
    Returns:
        Optional[Tuple[int, int]]: Tuple (start_line, end_line) mit Zeilennummern
        (0-basiert) oder None wenn kein Schema gefunden wird.
        
    Raises:
        Keine Exceptions - gibt None zurück bei Fehlern.
        
    Example:
        >>> prompt = "🧩 JSON-Ausgabeformat\\n{...}"
        >>> result = locate_json_schema(prompt)
        >>> result
        (1, 50)
        
    Note:
        - Start- und End-Zeile sind 0-basiert
        - End-Zeile ist inklusiv (letzte Zeile des Schemas)
        - Fallback: Nächste 200 Zeilen wenn kein explizites Ende gefunden wird
    """
    if not prompt_text:
        return None
    
    lines = prompt_text.split('\n')
    
    # Suche nach Schema-Markern (Priorität: spezifische Marker zuerst)
    start_line = None
    
    # PRIORITÄT 1: Suche nach vollständigem Marker mit Emoji (z.B. "🧩 JSON-Ausgabeformat")
    for i, line in enumerate(lines):
        if '🧩' in line and ('json' in line.lower() or 'ausgabeformat' in line.lower()):
            start_line = i
            break
    
    # PRIORITÄT 2: Suche nach Code-Block-Marker (```json)
    if start_line is None:
        for i, line in enumerate(lines):
            if '```json' in line.lower():
                start_line = i
                break
    
    # PRIORITÄT 3: Suche nach anderen Markern (aber nicht "Ausgabeformat" allein, da zu generisch)
    if start_line is None:
        markers = [
            'JSON-Struktur',
            'JSON-Ausgabeformat',  # Ohne Emoji, aber spezifisch
            'json-ausgabeformat'
        ]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(marker.lower() in line_lower for marker in markers):
                start_line = i
                break
    
    if start_line is None:
        return None
    
    # Suche nach Code-Block-Ende oder JSON-Struktur-Ende
    # WICHTIG: Wenn ```json gefunden wird, starte die Extraktion nach diesem Marker
    json_start_marker = None
    for i in range(start_line, len(lines)):
        if '```json' in lines[i].lower():
            json_start_marker = i
            start_line = i  # Starte Extraktion ab ```json Zeile
            break
    
    end_line = None
    for i in range(start_line, len(lines)):
        # Code-Block-Ende (nach ```json)
        if '```' in lines[i] and i > start_line:
            end_line = i
            break
        # Fallback: Suche nach letztem `}` (Top-Level-Ende)
        if lines[i].strip() == '}' and i > start_line + 10:
            # Prüfe ob es das Top-Level-Ende ist (vorherige Zeile sollte auch `}` sein oder leer)
            if i > 0 and (lines[i-1].strip().startswith('}') or lines[i-1].strip() == ''):
                end_line = i
                break
    
    if end_line is None:
        # Fallback: Nimm nächste 200 Zeilen
        end_line = min(start_line + 200, len(lines))
    
    return (start_line, end_line)


def extract_json_schema(prompt_text: str) -> Optional[Dict[str, Any]]:
    """
    Extrahiert das JSON-Schema aus dem Prompt-Text.
    
    Diese Funktion kombiniert Schema-Lokalisierung und JSON-Parsing:
    1. Lokalisiert den JSON-Schema-Abschnitt im Prompt
    2. Entfernt Code-Block-Marker (```json, ```)
    3. Entfernt JSON-Kommentare (//, /* */)
    4. Extrahiert vollständige JSON-Struktur (mit verschachtelten Klammern)
    5. Parst JSON und gibt strukturiertes Dict zurück
    
    Args:
        prompt_text: Der zu analysierende Prompt-Text. Muss nicht None sein.
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON-Dict mit vollständiger Struktur
        oder None wenn:
        - Kein Schema gefunden wird
        - JSON nicht parsbar ist (auch nach Reparatur-Versuch)
        
    Raises:
        Keine Exceptions - gibt None zurück bei Fehlern.
        
    Example:
        >>> prompt = "```json\\n{\\"document_metadata\\": {...}}\\n```"
        >>> result = extract_json_schema(prompt)
        >>> result
        {"document_metadata": {...}}
        
    Note:
        - Unterstützt verschachtelte JSON-Strukturen
        - Versucht unvollständiges JSON zu reparieren (fehlende Klammern)
        - Kommentare werden automatisch entfernt
    """
    location = locate_json_schema(prompt_text)
    if location is None:
        return None
    
    start_line, end_line = location
    lines = prompt_text.split('\n')
    schema_lines = lines[start_line:end_line+1]
    schema_text = '\n'.join(schema_lines)
    
    # Entferne Code-Block-Marker
    schema_text = re.sub(r'```json\s*', '', schema_text, flags=re.IGNORECASE)
    schema_text = re.sub(r'```\s*$', '', schema_text, flags=re.MULTILINE)
    
    # Entferne Schema-Marker (z.B. "🧩 JSON-Ausgabeformat")
    schema_text = re.sub(r'^[🧩\s]*JSON[-\s]*Ausgabeformat\s*$', '', schema_text, flags=re.IGNORECASE | re.MULTILINE)
    schema_text = re.sub(r'^[🧩\s]*JSON[-\s]*Struktur\s*$', '', schema_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Ersetze typografische Anführungszeichen durch normale (für JSON-Parsing)
    # Unicode: U+201C (") -> U+0022 ("), U+201D (") -> U+0022 (")
    schema_text = schema_text.replace('\u201C', '"').replace('\u201D', '"')
    schema_text = schema_text.replace('\u2018', "'").replace('\u2019', "'")
    
    # Entferne Kommentare
    schema_text = remove_json_comments(schema_text)
    
    # Extrahiere JSON-Struktur (zwischen { und }) - mit verschachtelten Klammern
    # Finde erste öffnende Klammer
    first_brace = schema_text.find('{')
    if first_brace == -1:
        return None
    
    # Zähle Klammern um vollständiges JSON zu finden
    brace_count = 0
    json_start = first_brace
    json_end = -1
    
    for i in range(first_brace, len(schema_text)):
        if schema_text[i] == '{':
            brace_count += 1
        elif schema_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    
    if json_end > json_start:
        json_str = schema_text[json_start:json_end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: Versuche unvollständiges JSON zu reparieren
            return repair_incomplete_json(json_str)
    
    return None


def remove_json_comments(text: str) -> str:
    """
    Entfernt JSON-Kommentare aus dem Text.
    
    Unterstützt:
    - Einzeilige Kommentare: // Kommentar
    - Mehrzeilige Kommentare: /* Kommentar */
    
    Args:
        text: Text mit möglichen JSON-Kommentaren
        
    Returns:
        Bereinigter Text ohne Kommentare
        
    Example:
        >>> remove_json_comments('{"key": "value"} // Kommentar')
        '{"key": "value"} '
    """
    # Entferne einzeilige Kommentare
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    # Entferne mehrzeilige Kommentare
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def repair_incomplete_json(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Versucht unvollständiges JSON zu reparieren.
    
    Diese Funktion versucht, häufig auftretende JSON-Fehler zu beheben:
    - Fehlende schließende geschweifte Klammern { }
    - Fehlende schließende eckige Klammern [ ]
    
    Die Funktion zählt öffnende und schließende Klammern und fügt
    fehlende schließende Klammern hinzu.
    
    Args:
        json_str: Unvollständiger JSON-String. Sollte nicht None sein.
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON-Dict nach Reparatur-Versuch
        oder None wenn:
        - JSON auch nach Reparatur nicht parsbar ist
        - Struktur zu komplex für automatische Reparatur
        
    Raises:
        Keine Exceptions - gibt None zurück bei Fehlern.
        
    Example:
        >>> repair_incomplete_json('{"key": "value"')
        {"key": "value"}
        >>> repair_incomplete_json('{"items": [1, 2, 3')
        {"items": [1, 2, 3]}
        
    Note:
        - Reparatur ist heuristisch und kann fehlschlagen
        - Funktioniert nur für einfache Fälle (fehlende Klammern)
        - Komplexe Strukturfehler werden nicht behoben
    """
    # Versuche fehlende schließende Klammern hinzuzufügen
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    
    if open_braces > close_braces:
        json_str += '}' * (open_braces - close_braces)
    
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    if open_brackets > close_brackets:
        json_str += ']' * (open_brackets - close_brackets)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def identify_top_level_keys(json_schema: Dict[str, Any]) -> List[str]:
    """
    Identifiziert die Top-Level-Keys des JSON-Schemas.
    
    Extrahiert alle Schlüssel auf der obersten Ebene des JSON-Schemas.
    Diese Keys repräsentieren die Hauptstruktur-Elemente (z.B. document_metadata,
    sections, steps) und werden für die Custom-Prompt-Generierung verwendet.
    
    Args:
        json_schema: Das JSON-Schema als Dict. Muss nicht leer sein.
        
    Returns:
        List[str]: Liste der Top-Level-Keys in der Reihenfolge wie im Dict.
        Leere Liste wenn json_schema leer ist.
        
    Raises:
        Keine Exceptions - gibt leere Liste zurück wenn Input leer.
        
    Example:
        >>> identify_top_level_keys({"document_metadata": {}, "sections": []})
        ["document_metadata", "sections"]
        >>> identify_top_level_keys({})
        []
        
    Note:
        - Reihenfolge entspricht der Dict-Reihenfolge (Python 3.7+)
        - Keys werden nicht sortiert oder gefiltert
    """
    return list(json_schema.keys())


def describe_json_structure(json_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erstellt eine strukturierte Beschreibung des JSON-Schemas.
    
    Analysiert das JSON-Schema rekursiv und erstellt eine vollständige
    Beschreibung mit:
    - Top-Level-Keys
    - Feld-Typen (object, array, string, etc.)
    - Verschachtelte Strukturen (rekursiv analysiert)
    
    Diese Beschreibung wird für die Custom-Prompt-Generierung verwendet,
    um dem LLM die verfügbaren JSON-Felder zu kommunizieren.
    
    Args:
        json_schema: Das JSON-Schema als Dict. Muss nicht leer sein.
        
    Returns:
        Dict[str, Any]: Strukturierte Beschreibung mit folgenden Keys:
        - top_level_keys: List[str] - Liste der Top-Level-Keys
        - field_types: Dict[str, str] - Mapping von Key zu Typ (object, array, str, etc.)
        - nested_structures: List[Dict] - Liste verschachtelter Strukturen mit:
          - key: str - Name des verschachtelten Feldes
          - structure: Dict - Rekursive Struktur-Beschreibung (für Objekte)
          - item_structure: Dict - Struktur-Beschreibung für Array-Items
        
    Raises:
        Keine Exceptions - gibt leere Struktur zurück wenn Input leer.
        
    Example:
        >>> result = describe_json_structure({"a": {}, "b": [{"x": 1}]})
        >>> result["top_level_keys"]
        ["a", "b"]
        >>> result["field_types"]
        {"a": "object", "b": "array"}
        >>> len(result["nested_structures"])
        2
        
    Note:
        - Rekursive Analyse (verschachtelte Strukturen werden vollständig analysiert)
        - Arrays von Objekten werden als item_structure dokumentiert
        - Maximale Tiefe ist durch Python-Rekursionslimit begrenzt
    """
    description = {
        'top_level_keys': list(json_schema.keys()),
        'field_types': {},
        'nested_structures': []
    }
    
    for key, value in json_schema.items():
        if isinstance(value, dict):
            description['field_types'][key] = 'object'
            # Rekursive Analyse verschachtelter Strukturen
            nested = describe_json_structure(value)
            description['nested_structures'].append({
                'key': key,
                'structure': nested
            })
        elif isinstance(value, list):
            description['field_types'][key] = 'array'
            if len(value) > 0 and isinstance(value[0], dict):
                # Array von Objekten
                description['nested_structures'].append({
                    'key': key,
                    'item_structure': describe_json_structure(value[0])
                })
        else:
            description['field_types'][key] = type(value).__name__
    
    return description

