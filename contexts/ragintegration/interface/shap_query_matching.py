"""
SHAP Analytics: Query-Matching Helper.

Warum existiert diese Datei?
- Router-Importe ziehen im Test-Kontext teils schwere Provider-Module nach (Google SDK, requests),
  was in Sandbox/CI zu Permission-Fehlern führen kann.
- Dieses Modul ist bewusst "pure python" und ohne externe Abhängigkeiten, damit Unit-Tests stabil sind.
"""

from __future__ import annotations

import re


def normalize_query_for_match(q: str) -> str:
    """Normalisiert eine Query für robustes Matching (Whitespace/Case/Punctuation)."""
    q = (q or "").strip().lower()
    # Collapse whitespace
    q = " ".join(q.split())
    # Remove most punctuation (keep umlauts/ß + alnum + space)
    q = re.sub(r"[^a-z0-9äöüß ]+", " ", q)
    q = " ".join(q.split())
    return q


def queries_match(a: str, b: str) -> bool:
    """Tolerantes Matching: equal oder contains (nach Normalisierung)."""
    na = normalize_query_for_match(a)
    nb = normalize_query_for_match(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return (na in nb) or (nb in na)



