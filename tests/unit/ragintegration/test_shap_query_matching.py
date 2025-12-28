"""
Unit Tests: SHAP Query Matching Helpers (Router).

Ziel: Sicherstellen, dass Query-Matching tolerant bleibt (Case/Whitespace/Punctuation),
damit /api/rag/analytics/shap stabil die passenden gespeicherten Source-Refs findet.
"""

from contexts.ragintegration.interface.shap_query_matching import (
    normalize_query_for_match,
    queries_match,
)


def test_normalize_query_for_match_basic():
    assert normalize_query_for_match("  Hallo   Welt ") == "hallo welt"
    assert normalize_query_for_match("Sicherheitshinweise!") == "sicherheitshinweise"
    assert normalize_query_for_match("ÄÖÜ ß") == "äöü ß"


def test_queries_match_exact_after_normalization():
    assert queries_match("  Wo  stehen  Hinweise? ", "wo stehen hinweise") is True
    assert queries_match("MONTAGE der Antriebseinheit", "montage der antriebseinheit") is True


def test_queries_match_contains_after_normalization():
    assert queries_match("Sicherheitshinweise zur Montage", "Sicherheitshinweise zur Montage der Antriebseinheit") is True
    assert queries_match("Sicherheitshinweise zur Montage der Antriebseinheit", "Sicherheitshinweise zur Montage") is True


def test_queries_match_false_on_empty():
    assert queries_match("", "abc") is False
    assert queries_match("abc", "") is False


