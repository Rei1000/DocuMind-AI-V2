"""
Infrastructure Layer: BM25 Text-Scoring Service

BM25 (Best Matching 25) ist ein klassischer Information-Retrieval-Algorithmus
für Text-Relevanz-Scoring. Besser als einfache Jaccard-Ähnlichkeit.
"""

from typing import List, Dict, Optional
import math
import re
from collections import Counter


class BM25Service:
    """
    Service für BM25 Text-Scoring.
    
    BM25 berechnet Relevanz-Scores basierend auf:
    - Term Frequency (TF): Wie oft erscheint ein Query-Term im Dokument?
    - Inverse Document Frequency (IDF): Wie selten ist ein Term?
    - Document Length: Längere Dokumente werden leicht bestraft
    
    Formel: BM25(q, d) = Σ IDF(qi) × (f(qi, d) × (k1 + 1)) / (f(qi, d) + k1 × (1 - b + b × |d| / avgdl))
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialisiere BM25 Service.
        
        Args:
            k1: Term Frequency Saturation Parameter (Standard: 1.5)
            b: Length Normalization Parameter (Standard: 0.75)
        """
        self.k1 = k1
        self.b = b
        self._document_frequencies: Dict[str, int] = {}  # Für IDF-Berechnung
        self._total_documents = 0
        self._average_document_length = 0.0
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisiere Text in Wörter.
        
        Args:
            text: Text zum Tokenisieren
            
        Returns:
            Liste von Tokens (Wörtern)
        """
        # Entferne Sonderzeichen, konvertiere zu Kleinbuchstaben
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split auf Whitespace
        tokens = text.split()
        # Filtere leere Tokens
        return [token for token in tokens if len(token) > 0]
    
    def _calculate_idf(self, term: str) -> float:
        """
        Berechne Inverse Document Frequency (IDF) für einen Term.
        
        Args:
            term: Der Term
            
        Returns:
            IDF-Wert
        """
        if term not in self._document_frequencies or self._total_documents == 0:
            return 0.0
        
        df = self._document_frequencies[term]  # Document Frequency
        # IDF = log((N - df + 0.5) / (df + 0.5))
        # N = total_documents
        idf = math.log((self._total_documents - df + 0.5) / (df + 0.5))
        return max(0.0, idf)  # Stelle sicher dass IDF >= 0
    
    def calculate_score(self, query: str, document: str, corpus: Optional[List[str]] = None) -> float:
        """
        Berechne BM25 Score für Query-Document-Paar.
        
        Args:
            query: Die Suchanfrage
            document: Das Dokument
            corpus: Optional: Korpus für IDF-Berechnung (falls None, wird vereinfachte IDF verwendet)
            
        Returns:
            BM25 Score (normalisiert auf 0-1)
        """
        if not query or not document:
            return 0.0
        
        # Tokenisiere Query und Document
        query_tokens = self._tokenize(query)
        document_tokens = self._tokenize(document)
        
        if not query_tokens or not document_tokens:
            return 0.0
        
        # Berechne Term Frequencies im Document
        document_term_freq = Counter(document_tokens)
        document_length = len(document_tokens)
        
        # Berechne durchschnittliche Document-Länge (falls Korpus vorhanden)
        if corpus:
            self._update_document_frequencies(corpus)
            avg_doc_length = self._average_document_length
        else:
            # Fallback: Verwende Document-Länge selbst als Durchschnitt
            avg_doc_length = document_length
        
        # Berechne BM25 Score
        score = 0.0
        for term in query_tokens:
            if term not in document_term_freq:
                continue  # Term nicht im Document → Score = 0 für diesen Term
            
            # Term Frequency im Document
            tf = document_term_freq[term]
            
            # IDF (vereinfacht wenn kein Korpus)
            if corpus:
                idf = self._calculate_idf(term)
            else:
                # Fallback: Einfache IDF (log-basiert)
                idf = math.log(1.0 + (1.0 / (tf + 1.0)))
            
            # BM25 Formel
            # BM25(q, d) = IDF(q) × (TF(q, d) × (k1 + 1)) / (TF(q, d) + k1 × (1 - b + b × |d| / avgdl))
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (document_length / avg_doc_length))
            term_score = idf * (numerator / denominator)
            
            score += term_score
        
        # Normalisiere Score auf 0-1 (einfache Sigmoid-Normalisierung)
        # Verwende tanh für Normalisierung (0-1 Bereich)
        normalized_score = math.tanh(score / 10.0)  # Division durch 10 für bessere Normalisierung
        
        return max(0.0, min(1.0, normalized_score))
    
    def calculate_batch_scores(self, query: str, documents: List[str]) -> List[float]:
        """
        Berechne BM25 Scores für mehrere Dokumente.
        
        Args:
            query: Die Suchanfrage
            documents: Liste von Dokumenten
            
        Returns:
            Liste von BM25 Scores (normalisiert auf 0-1)
        """
        if not documents:
            return []
        
        # Update Document Frequencies für IDF-Berechnung
        self._update_document_frequencies(documents)
        
        # Berechne Scores für alle Dokumente
        scores = [self.calculate_score(query, doc, documents) for doc in documents]
        
        return scores
    
    def _update_document_frequencies(self, corpus: List[str]):
        """
        Update Document Frequencies für IDF-Berechnung.
        
        Args:
            corpus: Liste von Dokumenten
        """
        self._total_documents = len(corpus)
        self._document_frequencies = {}
        
        # Tokenisiere alle Dokumente
        all_tokens = []
        total_length = 0
        
        for doc in corpus:
            tokens = self._tokenize(doc)
            all_tokens.extend(tokens)
            total_length += len(tokens)
            
            # Zähle unique Terms pro Dokument
            unique_terms = set(tokens)
            for term in unique_terms:
                self._document_frequencies[term] = self._document_frequencies.get(term, 0) + 1
        
        # Berechne durchschnittliche Document-Länge
        if self._total_documents > 0:
            self._average_document_length = total_length / self._total_documents
        else:
            self._average_document_length = 0.0

