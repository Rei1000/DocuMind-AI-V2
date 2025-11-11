"""
Infrastructure Layer: Vision Data Extractor Adapter

Extrahiert strukturierte Daten aus Vision AI Processing Results.
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from contexts.ragintegration.domain.value_objects import ChunkMetadata
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.infrastructure.services import DocumentTypeSpecificChunkingService


class VisionDataExtractorAdapter:
    """Adapter für die Extraktion von Vision AI Daten."""
    
    def __init__(self):
        """Initialisiert den Vision Data Extractor."""
        self.document_type_chunking_service = DocumentTypeSpecificChunkingService()
    
    def extract_chunks_from_vision_data(
        self, 
        vision_data: List[Dict[str, Any]], 
        document_id: int,
        document_type: str
    ) -> List[DocumentChunk]:
        """
        Extrahiert strukturierte Chunks aus Vision AI Daten.
        
        Verwendet die neue strukturierte Chunking-Strategie für bessere Ergebnisse.
        """
        chunks = []
        
        # WICHTIG: Für Fachartikel können wir seitenweise verarbeiten (wie bei Arbeitsanweisungen)
        # ABER: Wenn document_metadata/abstract nur auf Seite 1 vorhanden sind, sollten wir zusammenführen
        # für bessere RAG-Qualität (alle sections in einem Kontext)
        if document_type.lower() in ['fachartikel', 'research_article', 'article']:
            # Prüfe ob wir zusammenführen sollten:
            # - Wenn mehrere Seiten vorhanden sind UND
            # - Jede Seite hat document_metadata/sections → Zusammenführen für bessere RAG-Qualität
            # - Sonst: Seitenweise verarbeiten (wie bei Arbeitsanweisungen)
            
            # Prüfe ob alle Seiten die gleiche Struktur haben (document_metadata + sections)
            # WICHTIG: Nur zusammenführen wenn mehrere Seiten vorhanden sind UND
            # jede Seite document_metadata oder sections hat (für bessere RAG-Qualität)
            should_merge = False
            if len(vision_data) > 1:
                # Prüfe ob alle Seiten JSON-Responses haben
                all_have_json = all('json_response' in section_data for section_data in vision_data)
                if all_have_json:
                    # Prüfe ob mindestens eine Seite document_metadata oder sections hat
                    has_structure = False
                    for section_data in vision_data:
                        json_response = section_data.get('json_response', {})
                        if isinstance(json_response, str):
                            try:
                                json_response = json.loads(json_response)
                            except:
                                continue
                        if isinstance(json_response, dict):
                            if 'document_metadata' in json_response or 'sections' in json_response:
                                has_structure = True
                                break
                    should_merge = has_structure
            
            if should_merge:
                # Zusammenführen für bessere RAG-Qualität (alle sections in einem Kontext)
                print(f"DEBUG: Zusammenführen von {len(vision_data)} Seiten für Fachartikel")
                merged_json = self._merge_research_article_json(vision_data)
                if merged_json:
                    # WICHTIG: page_number=1 wird verwendet, aber _chunk_research_article
                    # verwendet page_number_mapping und all_page_numbers aus merged_json
                    structured_chunks = self.document_type_chunking_service.create_chunks_from_vision_data(
                        merged_json, 
                        document_id,
                        document_type,
                        page_number=1  # Wird ignoriert, da page_number_mapping verwendet wird
                    )
                    print(f"DEBUG: {len(structured_chunks)} Chunks aus zusammengeführtem JSON erstellt")
                    chunks.extend(structured_chunks)
                else:
                    # Fallback: Seitenweise verarbeiten
                    for section_data in vision_data:
                        if 'json_response' in section_data:
                            vision_json = self._convert_to_vision_json(section_data)
                            page_number = section_data.get('page_number', 1)
                            structured_chunks = self.document_type_chunking_service.create_chunks_from_vision_data(
                                vision_json, 
                                document_id,
                                document_type,
                                page_number=page_number
                            )
                            chunks.extend(structured_chunks)
            else:
                # Seitenweise verarbeiten (wie bei Arbeitsanweisungen)
                print(f"DEBUG: Seitenweise Verarbeitung von {len(vision_data)} Seiten für Fachartikel")
                for section_data in vision_data:
                    if 'json_response' in section_data:
                        vision_json = self._convert_to_vision_json(section_data)
                        page_number = section_data.get('page_number', 1)
                        structured_chunks = self.document_type_chunking_service.create_chunks_from_vision_data(
                            vision_json, 
                            document_id,
                            document_type,
                            page_number=page_number
                        )
                        print(f"DEBUG: Seite {page_number}: {len(structured_chunks)} Chunks erstellt")
                        chunks.extend(structured_chunks)
        else:
            # Für andere Dokumenttypen: Verarbeite jede Seite einzeln
            for section_data in vision_data:
                # Prüfe ob es sich um Vision-JSON-Daten handelt
                if 'json_response' in section_data:
                    # Verwende dokumenttyp-spezifische Chunking-Strategie
                    vision_json = self._convert_to_vision_json(section_data)
                    # WICHTIG: Extrahiere page_number aus section_data und übergebe es
                    page_number = section_data.get('page_number', 1)
                    structured_chunks = self.document_type_chunking_service.create_chunks_from_vision_data(
                        vision_json, 
                        document_id,
                        document_type,
                        page_number=page_number  # WICHTIG: page_number übergeben
                    )
                    chunks.extend(structured_chunks)
                elif 'text' in section_data:
                    # Fallback zu einfachem Chunk
                    chunk = self._create_simple_chunk(
                        text=section_data['text'],
                        document_id=document_id,
                        document_type=document_type
                    )
                    chunks.append(chunk)
                else:
                    # Normale Section-basierte Verarbeitung
                    section_chunks = self._extract_section_chunks(
                        section_data, 
                        document_id, 
                        document_type
                    )
                    chunks.extend(section_chunks)
        
        return chunks
    
    def _merge_research_article_json(self, vision_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Führt JSON-Responses aller Seiten für Fachartikel zusammen.
        
        Für Fachartikel werden die JSON-Responses aller Seiten zu einem einzigen
        JSON-Objekt zusammengeführt, da die Chunking-Strategie die vollständige
        Struktur (document_metadata, sections, etc.) in einem Objekt erwartet.
        
        Returns:
            Dict mit merged JSON und page_number_mapping für Sections
        """
        if not vision_data:
            return None
        
        merged = {}
        page_number_mapping = {}  # Track welche Sections von welchen Seiten kommen
        all_page_numbers = []  # Alle Seiten, die verarbeitet wurden
        
        # Führe alle JSON-Responses zusammen
        for section_data in vision_data:
            if 'json_response' not in section_data:
                continue
            
            page_number = section_data.get('page_number', 1)
            all_page_numbers.append(page_number)
            
            json_response = section_data.get("json_response", {})
            if isinstance(json_response, str):
                # WICHTIG: Entferne Markdown-Code-Blöcke (```json ... ```) falls vorhanden
                cleaned_json = json_response.strip()
                if cleaned_json.startswith("```json"):
                    cleaned_json = cleaned_json[7:].strip()
                elif cleaned_json.startswith("```"):
                    cleaned_json = cleaned_json[3:].strip()
                if cleaned_json.endswith("```"):
                    cleaned_json = cleaned_json[:-3].strip()
                try:
                    json_response = json.loads(cleaned_json)
                except json.JSONDecodeError:
                    continue
            
            # Führe document_metadata zusammen (nimm die erste nicht-leere)
            if "document_metadata" in json_response and json_response["document_metadata"]:
                if "document_metadata" not in merged or not merged["document_metadata"]:
                    merged["document_metadata"] = json_response["document_metadata"]
                    # Metadata kommt von der ersten Seite
                    merged["_metadata_page"] = page_number
            
            # Führe abstract zusammen (nimm die erste nicht-leere)
            if "abstract" in json_response and json_response["abstract"]:
                if "abstract" not in merged or not merged["abstract"]:
                    merged["abstract"] = json_response["abstract"]
                    # Abstract kommt von der ersten Seite
                    merged["_abstract_page"] = page_number
            
            # Führe sections zusammen (append, da jede Seite eigene Sections haben kann)
            # WICHTIG: Track welche Sections von welchen Seiten kommen
            # WICHTIG: Vermeide Duplikate - wenn Section bereits existiert, füge nur page_number hinzu
            if "sections" in json_response:
                if "sections" not in merged:
                    merged["sections"] = []
                
                # WICHTIG: Füge ALLE Sections hinzu, auch wenn sie die gleiche section_number haben
                # Grund: Verschiedene Seiten können Sections mit gleicher Nummer haben, aber unterschiedlichem Inhalt
                # Beispiel: Seite 1 hat Section 1 "Einleitung", Seite 7 hat Section 1 "HAUPTAUFSATZ"
                # Lösung: Füge alle Sections hinzu und tracke page_numbers für jede Section
                for section in json_response["sections"]:
                    section_num = section.get("section_number", "?")
                    # Erstelle eindeutigen Key: section_number + page_number (falls Section bereits existiert)
                    section_key = f"section_{section_num}_page_{page_number}"
                    
                    # Track page_number für diese Section
                    # Verwende section_number als Basis-Key für page_number_mapping
                    base_key = f"section_{section_num}"
                    if base_key not in page_number_mapping:
                        page_number_mapping[base_key] = []
                    if page_number not in page_number_mapping[base_key]:
                        page_number_mapping[base_key].append(page_number)
                    
                    # Füge Section hinzu (auch wenn section_number bereits existiert)
                    # WICHTIG: Füge page_number zur Section hinzu, damit wir später wissen, von welcher Seite sie kommt
                    section_with_page = section.copy()
                    section_with_page["_source_page"] = page_number
                    merged["sections"].append(section_with_page)
                    print(f"DEBUG: Section {section_num} von Seite {page_number} hinzugefügt (Key: {section_key})")
            
            # Führe key_findings zusammen (append)
            if "key_findings" in json_response:
                if "key_findings" not in merged:
                    merged["key_findings"] = []
                merged["key_findings"].extend(json_response["key_findings"])
            
            # Führe software_and_tools zusammen (append)
            if "software_and_tools" in json_response:
                if "software_and_tools" not in merged:
                    merged["software_and_tools"] = []
                merged["software_and_tools"].extend(json_response["software_and_tools"])
            
            # Führe references zusammen (append)
            if "references" in json_response:
                if "references" not in merged:
                    merged["references"] = []
                merged["references"].extend(json_response["references"])
        
        # Speichere page_number_mapping und all_page_numbers im merged JSON
        # (werden später in _chunk_research_article verwendet)
        merged["_page_number_mapping"] = page_number_mapping
        merged["_all_page_numbers"] = sorted(list(set(all_page_numbers)))
        
        print(f"DEBUG: _merge_research_article_json: Merged keys={list(merged.keys())}, sections_count={len(merged.get('sections', []))}, pages={merged.get('_all_page_numbers', [])}")
        return merged if merged else None
    
    def _convert_to_vision_json(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konvertiert Vision-Daten in das erwartete JSON-Format für dokumenttyp-spezifisches Chunking.
        
        Die echten Vision-Daten haben bereits die korrekte Struktur mit:
        - document_metadata
        - process_steps
        - compliance_requirements
        - critical_rules
        - referenced_documents
        
        WICHTIG: Entfernt Markdown-Code-Blöcke (```json ... ```) falls vorhanden.
        """
        json_response = section_data.get("json_response", {})
        page_number = section_data.get("page_number", 1)
        
        if isinstance(json_response, str):
            # WICHTIG: Entferne Markdown-Code-Blöcke falls vorhanden
            # Beispiel: "```json\n{...}\n```" → "{...}"
            cleaned_json = json_response.strip()
            if cleaned_json.startswith("```json"):
                # Entferne ```json am Anfang
                cleaned_json = cleaned_json[7:].strip()
            elif cleaned_json.startswith("```"):
                # Entferne ``` am Anfang (falls kein "json" Label)
                cleaned_json = cleaned_json[3:].strip()
            
            if cleaned_json.endswith("```"):
                # Entferne ``` am Ende
                cleaned_json = cleaned_json[:-3].strip()
            
            try:
                json_response = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                print(f"WARNING: _convert_to_vision_json: JSON-Parse-Fehler für Seite {page_number}: {e}")
                print(f"DEBUG: Erste 200 Zeichen des Strings: {cleaned_json[:200]}")
                json_response = {}
        
        # Die echten Vision-Daten haben bereits die korrekte Struktur
        # Wir geben sie direkt zurück für das neue Chunking
        print(f"DEBUG: _convert_to_vision_json: page_number={page_number}, keys={list(json_response.keys()) if isinstance(json_response, dict) else 'NOT A DICT'}")
        return json_response
    
    def _create_simple_chunk(self, text: str, document_id: int, document_type: str) -> DocumentChunk:
        """Erstellt einen einfachen Chunk aus Text."""
        from contexts.ragintegration.domain.value_objects import ChunkMetadata
        from datetime import datetime
        
        # Erstelle Chunk Metadata
        metadata = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=["Test Section"],
            document_type_id=1,
            confidence=1.0,
            chunk_type='text',
            token_count=len(text) // 4
        )
        
        # Erstelle DocumentChunk
        chunk = DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_chunk_0",
            chunk_text=text,
            metadata=metadata,
            qdrant_point_id=f"qdrant_{document_id}_0",
            created_at=datetime.utcnow()
        )
        
        return chunk
    
    def _extract_section_chunks(
        self, 
        section_data: Dict[str, Any], 
        document_id: int,
        document_type: str
    ) -> List[DocumentChunk]:
        """Extrahiert Chunks aus einem Section."""
        chunks = []
        
        # Extrahiere Basis-Informationen
        section_title = section_data.get('section_title', 'Unbekannter Abschnitt')
        content = section_data.get('content', '')
        start_page = section_data.get('start_page') or 1
        end_page = section_data.get('end_page') or start_page
        
        # Sicherstellen dass start_page und end_page nicht None sind
        if start_page is None:
            start_page = 1
        if end_page is None:
            end_page = start_page
        
        # Erstelle Heading Hierarchy
        heading_hierarchy = self._build_heading_hierarchy(section_data)
        
        # Teile Content in Chunks auf
        content_chunks = self._split_content_into_chunks(content)
        
        for i, chunk_text in enumerate(content_chunks):
            # Erstelle Chunk Metadata
            metadata = ChunkMetadata(
                page_numbers=list(range(start_page, end_page + 1)),
                heading_hierarchy=heading_hierarchy,
                document_type=document_type,
                confidence_score=section_data.get('confidence_score', 1.0),
                chunk_type='vision_extracted',
                token_count=self._estimate_token_count(chunk_text)
            )
            
            # Erstelle DocumentChunk
            chunk = DocumentChunk(
                id=None,  # Wird von Repository gesetzt
                indexed_document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=i,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _build_heading_hierarchy(self, section_data: Dict[str, Any]) -> List[str]:
        """Baut Heading Hierarchy aus Section Data."""
        hierarchy = []
        
        # Füge Section Title hinzu
        section_title = section_data.get('section_title', '')
        if section_title:
            hierarchy.append(section_title)
        
        # Füge Subsection hinzu falls vorhanden
        subsection = section_data.get('subsection', '')
        if subsection:
            hierarchy.append(subsection)
        
        return hierarchy
    
    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """Teilt Content in Chunks auf."""
        if not content:
            return []
        
        # Einfache Aufteilung nach Sätzen
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Füge Punkt hinzu falls nicht vorhanden
            if not sentence.endswith('.'):
                sentence += '.'
            
            # Prüfe ob neuer Chunk nötig ist
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Füge letzten Chunk hinzu
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _estimate_token_count(self, text: str) -> int:
        """Schätzt Token-Anzahl für Text."""
        # Grobe Schätzung: 1 Token ≈ 4 Zeichen
        return len(text) // 4
    
    def extract_structured_data(self, vision_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrahiert strukturierte Daten aus Vision AI Response."""
        structured_data = {
            'sections': [],
            'tables': [],
            'lists': [],
            'key_value_pairs': [],
            'metadata': {}
        }
        
        for section in vision_data:
            # Extrahiere Section-Informationen
            section_info = {
                'title': section.get('section_title', ''),
                'content': section.get('content', ''),
                'page_range': f"{section.get('start_page', 1)}-{section.get('end_page', 1)}",
                'confidence': section.get('confidence_score', 1.0)
            }
            structured_data['sections'].append(section_info)
            
            # Extrahiere Tabellen falls vorhanden
            if 'tables' in section:
                structured_data['tables'].extend(section['tables'])
            
            # Extrahiere Listen falls vorhanden
            if 'lists' in section:
                structured_data['lists'].extend(section['lists'])
            
            # Extrahiere Key-Value Paare falls vorhanden
            if 'key_value_pairs' in section:
                structured_data['key_value_pairs'].extend(section['key_value_pairs'])
        
        # Berechne Metadaten
        structured_data['metadata'] = {
            'total_sections': len(structured_data['sections']),
            'total_tables': len(structured_data['tables']),
            'total_lists': len(structured_data['lists']),
            'total_key_value_pairs': len(structured_data['key_value_pairs']),
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        return structured_data
    
    def validate_vision_data(self, vision_data: List[Dict[str, Any]]) -> bool:
        """Validiert Vision AI Daten."""
        try:
            if not isinstance(vision_data, list):
                return False
            
            for section in vision_data:
                if not isinstance(section, dict):
                    return False
                
                # Prüfe erforderliche Felder
                required_fields = ['section_title', 'content']
                for field in required_fields:
                    if field not in section:
                        return False
                
                # Prüfe Datentypen
                if not isinstance(section['section_title'], str):
                    return False
                if not isinstance(section['content'], str):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_extraction_summary(self, vision_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der extrahierten Daten zurück."""
        if not vision_data:
            return {'error': 'Keine Vision Daten verfügbar'}
        
        total_sections = len(vision_data)
        total_content_length = sum(len(section.get('content', '')) for section in vision_data)
        avg_confidence = sum(section.get('confidence_score', 1.0) for section in vision_data) / total_sections
        
        return {
            'total_sections': total_sections,
            'total_content_length': total_content_length,
            'average_confidence': round(avg_confidence, 2),
            'page_range': f"{min(section.get('start_page', 1) for section in vision_data)}-{max(section.get('end_page', 1) for section in vision_data)}",
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
