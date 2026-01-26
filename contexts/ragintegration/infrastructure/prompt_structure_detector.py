"""
Prompt Structure Detector Utility

Zentrale Utility-Funktionen für die robuste Erkennung von Prompt-Struktur-Typen.

CR-P2.1: Eliminiert Code-Duplikation zwischen ai_service.py und services.py.
"""

import json
import re
from typing import Optional


def detect_prompt_structure_type(prompt_text: str) -> Optional[str]:
    """
    Erkennt den Prompt-Struktur-Typ robust durch JSON-Analyse.
    
    Unterstützt verschiedene Format-Varianten:
    - Case-Varianten: snake_case, camelCase, PascalCase, MixedCase
    - Kommentare werden ignoriert (// und /* */)
    - Unvollständige Strukturen werden erkannt
    - Multiline-Prompts werden unterstützt
    
    Args:
        prompt_text: Der zu analysierende Prompt-Text
        
    Returns:
        Typ-String: "flowchart", "work_instruction", "sop", "research_article", "datasheet", None
        None wenn kein Typ erkannt werden kann
        
    Examples:
        >>> detect_prompt_structure_type('{"nodes": [...]}')
        'flowchart'
        >>> detect_prompt_structure_type('{"steps": [{"step_number": 1}]}')
        'work_instruction'
        >>> detect_prompt_structure_type('{"ProcessSteps": [...]}')
        'sop'
    """
    if not prompt_text:
        return None
    
    prompt_clean = remove_json_comments(prompt_text)
    
    try:
        data = json.loads(prompt_clean)
    except (json.JSONDecodeError, ValueError):
        return detect_type_by_string_pattern(prompt_text)
    
    if not isinstance(data, dict):
        return detect_type_by_string_pattern(prompt_text)
    
    keys_lower = {k.lower(): k for k in data.keys()}
    
    if "nodes" in keys_lower or any("node" in k.lower() and "list" in k.lower() for k in keys_lower):
        return "flowchart"
    
    if "sections" in keys_lower and "document_metadata" in keys_lower:
        return "research_article"
    
    if "technical_specifications" in keys_lower:
        return "datasheet"
    
    if "requirements" in keys_lower and (
        "terms_and_definitions" in keys_lower
        or "scope_statements" in keys_lower
        or "page_text_de" in keys_lower
        or "sections_on_page" in keys_lower
        or "test_methods" in keys_lower
    ):
        return "technical_standard"
    
    if "process_steps" in keys_lower or any("process" in k.lower() and "step" in k.lower() for k in keys_lower):
        return "sop"
    
    if "steps" in keys_lower:
        steps_value = data[keys_lower["steps"]]
        if isinstance(steps_value, list) and len(steps_value) > 0:
            first_step = steps_value[0]
            if isinstance(first_step, dict):
                step_keys_lower = {k.lower(): k for k in first_step.keys()}
                if "step_number" in step_keys_lower or "stepnumber" in step_keys_lower:
                    return "work_instruction"
                if "description" in step_keys_lower:
                    return "work_instruction"
        return "work_instruction"
    
    return detect_type_by_string_pattern(prompt_text)


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
        
    Examples:
        >>> remove_json_comments('{"key": "value"} // Kommentar')
        '{"key": "value"} '
        >>> remove_json_comments('{"key": "value"} /* Kommentar */')
        '{"key": "value"} '
    """
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def detect_type_by_string_pattern(prompt_text: str) -> Optional[str]:
    """
    Fallback: String-Pattern-Matching für nicht-JSON Prompts.
    
    Wird verwendet wenn JSON-Parsing fehlschlägt oder der Prompt
    keine gültige JSON-Struktur enthält.
    
    Args:
        prompt_text: Der zu analysierende Prompt-Text
        
    Returns:
        Typ-String: "flowchart", "work_instruction", "sop", "research_article", "datasheet", None
        None wenn kein Typ erkannt werden kann
    """
    prompt_lower = prompt_text.lower()
    
    if re.search(r'["\']nodes["\']', prompt_text) or re.search(r'["\']nodelist["\']', prompt_lower):
        return "flowchart"
    
    if re.search(r'["\']sections["\']', prompt_text) and re.search(r'["\']document_metadata["\']', prompt_text):
        return "research_article"
    
    if re.search(r'["\']technical_specifications["\']', prompt_lower):
        return "datasheet"
    
    if re.search(r'["\']requirements["\']', prompt_lower) and (
        re.search(r'["\']terms_and_definitions["\']', prompt_lower)
        or re.search(r'["\']scope_statements["\']', prompt_lower)
        or re.search(r'["\']page_text_de["\']', prompt_lower)
        or re.search(r'["\']sections_on_page["\']', prompt_lower)
        or re.search(r'["\']test_methods["\']', prompt_lower)
    ):
        return "technical_standard"
    
    if re.search(r'["\']process_steps["\']', prompt_lower) or re.search(r'["\']processsteps["\']', prompt_lower):
        return "sop"
    
    if re.search(r'["\']steps["\']', prompt_text):
        if re.search(r'["\']step_number["\']', prompt_text) or re.search(r'["\']stepnumber["\']', prompt_lower):
            return "work_instruction"
        return "work_instruction"
    
    return None

