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
        # Deutsche Stop-Wörter (häufige Wörter die wenig Bedeutung haben)
        stop_words = {
            'der', 'die', 'das', 'und', 'oder', 'aber', 'wie', 'ich', 'du', 'er', 'sie', 'es',
            'wir', 'ihr', 'sie', 'ein', 'eine', 'einen', 'einem', 'einer', 'eines',
            'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'hat', 'haben', 'hatte', 'hatten',
            'mit', 'von', 'zu', 'für', 'auf', 'in', 'an', 'bei', 'über', 'unter', 'durch',
            'dass', 'dass', 'wenn', 'ob', 'als', 'während', 'nach', 'vor', 'seit', 'bis',
            'auch', 'noch', 'nur', 'schon', 'noch', 'immer', 'nie', 'oft', 'manchmal',
            'sehr', 'viel', 'wenig', 'mehr', 'weniger', 'am', 'zum', 'zur', 'im', 'ins'
        }
        
        # Entferne Sonderzeichen, konvertiere zu Kleinbuchstaben
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split auf Whitespace
        tokens = text.split()
        # Filtere leere Tokens und Stop-Wörter
        return [token for token in tokens if len(token) > 0 and token not in stop_words]
    
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
        matched_terms = 0
        for term in query_tokens:
            if term not in document_term_freq:
                # NEU: Prüfe auch Teilwort-Matches (für bessere Abdeckung)
                # Suche nach Teilwort-Matches im Dokument
                partial_match = False
                for doc_term in document_term_freq.keys():
                    if term in doc_term or doc_term in term:
                        # Teilwort-Match gefunden - verwende niedrigeren Score
                        tf = document_term_freq[doc_term]
                        idf = math.log(1.0 + (1.0 / (tf + 1.0))) * 0.5  # Reduzierter Score für Teilwort-Match
                        numerator = tf * (self.k1 + 1)
                        denominator = tf + self.k1 * (1 - self.b + self.b * (document_length / avg_doc_length))
                        term_score = idf * (numerator / denominator) * 0.3  # Weitere Reduktion für Teilwort
                        score += term_score
                        partial_match = True
                        matched_terms += 1
                        break
                
                if not partial_match:
                    continue  # Term nicht im Document → Score = 0 für diesen Term
                # Partial-Match wurde bereits bewertet, nächster Query-Term
                continue
            
            matched_terms += 1
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
        
        # NEU: Wenn keine Terms gematcht wurden, aber Query und Document beide existieren,
        # gebe einen minimalen Score zurück (nicht 0.0)
        if matched_terms == 0 and query_tokens and document_tokens:
            # Minimaler Score basierend auf Dokument-Länge (längere Dokumente = höherer minimaler Score)
            min_score = min(0.01, document_length / 10000.0)  # Max 0.01 für sehr lange Dokumente
            score = min_score
        
        # Normalisiere Score auf 0-1
        # WICHTIG: BM25 Scores können sehr unterschiedlich sein (0.1-100+)
        # Verwende eine bessere Normalisierung die auch kleine Scores berücksichtigt
        if score <= 0:
            return 0.0
        
        # Verwende Sättigungs-Normalisierung statt Sigmoid.
        # Grund: Sigmoid liefert bei kleinen positiven Scores ~0.5 und macht
        # nahezu alle Text-Scores ununterscheidbar. Das verschlechtert Ranking
        # für kurze Fachbegriffe stark.
        # score=0.0 -> 0.0, score=1.0 -> 0.5, score=3.0 -> 0.75
        normalization_factor = 1.0
        normalized_score = score / (score + normalization_factor)
        
        # Option 2: Min-Max Normalisierung (falls Score-Bereich bekannt)
        # Für jetzt verwenden wir Sigmoid, da sie robuster ist
        
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

