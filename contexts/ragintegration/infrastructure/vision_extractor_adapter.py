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
        
        for section_data in vision_data:
            # Prüfe ob es sich um Vision-JSON-Daten handelt
            if 'json_response' in section_data:
                # Verwende dokumenttyp-spezifische Chunking-Strategie
                vision_json = self._convert_to_vision_json(section_data)
                structured_chunks = self.document_type_chunking_service.create_chunks_from_vision_data(
                    vision_json, 
                    document_id,
                    document_type
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
    
    def _convert_to_vision_json(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konvertiert Vision-Daten in das erwartete JSON-Format für dokumenttyp-spezifisches Chunking.
        
        Die echten Vision-Daten haben bereits die korrekte Struktur mit:
        - document_metadata
        - process_steps
        - compliance_requirements
        - critical_rules
        - referenced_documents
        """
        json_response = section_data.get("json_response", {})
        page_number = section_data.get("page_number", 1)
        
        if isinstance(json_response, str):
            try:
                json_response = json.loads(json_response)
            except json.JSONDecodeError:
                json_response = {}
        
        # Die echten Vision-Daten haben bereits die korrekte Struktur
        # Wir müssen sie nur in das erwartete Format umwandeln
        return {
            "pages": [
                {
                    "page_number": page_number,
                    "content": json_response
                }
            ]
        }
    
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
        start_page = section_data.get('start_page', 1)
        end_page = section_data.get('end_page', start_page)
        
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
