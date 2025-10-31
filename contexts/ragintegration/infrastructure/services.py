"""
Infrastructure Services für RAG Integration

Implementiert verschiedene Services für Chunking, Embedding und AI-Integration.
"""
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import ChunkMetadata, SourceReference


# ===== BESTEHENDE SERVICES =====

class HeadingAwareChunkingServiceImpl:
    """Service für Heading-Aware Chunking."""
    
    def __init__(self, vision_extractor=None):
        self.heading_pattern = re.compile(r'^(\d+\.?\s*[A-ZÄÖÜ][^\n]*)$', re.MULTILINE)
        self.vision_extractor = vision_extractor
    
    def create_chunks(self, document_pages: List[Any]) -> List[DocumentChunk]:
        """Erstelle Chunks basierend auf Überschriften."""
        chunks = []
        
        for page in document_pages:
            # Extrahiere JSON-Response falls vorhanden
            json_response = getattr(page, 'json_response', {})
            
            if isinstance(json_response, str):
                try:
                    json_response = json.loads(json_response)
                except json.JSONDecodeError:
                    json_response = {}
            
            # Erstelle einfachen Chunk
            if json_response.get("text"):
                chunk = DocumentChunk(
                    id=None,
                    indexed_document_id=1,  # Mock ID
                    chunk_id=f"chunk_{len(chunks)}",
                    chunk_text=json_response["text"],
                    metadata=ChunkMetadata(
                        page_numbers=[1],
                        heading_hierarchy=[],
                        chunk_type="text",
                        token_count=len(json_response["text"].split()),
                        sentence_count=len(json_response["text"].split('.')),
                        has_overlap=False,
                        overlap_sentence_count=0
                    ),
                    qdrant_point_id=str(uuid.uuid4()),
                    created_at=datetime.now()
                )
                chunks.append(chunk)
        
        return chunks


# ===== NEUE STRUKTURIERTE CHUNKING SERVICES =====


class MultiQueryServiceImpl:
    """Service für Multi-Query Expansion."""
    
    def __init__(self):
        pass
    
    def generate_queries(self, question: str) -> List[str]:
        """Generiere mehrere Query-Varianten."""
        # Vereinfachte Implementierung
        return [question]


class StructuredDataExtractorServiceImpl:
    """Service für strukturierte Datenextraktion."""
    
    def __init__(self):
        pass
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extrahiere strukturierte Daten aus Text."""
        # Vereinfachte Implementierung
        return {"text": text}


class DocumentTypeSpecificChunkingService:
    """
    Dokumenttyp-spezifische Chunking-Strategien basierend auf RAG-Anything Best Practices.
    
    Nutzt die Prompt-Templates aus der Datenbank, um die JSON-Struktur zu verstehen
    und optimale Chunking-Strategien für jeden Dokumenttyp anzuwenden.
    """
    
    def __init__(self):
        """Initialisiert den dokumenttyp-spezifischen Chunking Service."""
        self.chunking_strategies = {
            "SOP": self._chunk_sop_document,
            "ARBEITSANWEISUNG": self._chunk_work_instruction,
            "FLUSSDIAGRAMM": self._chunk_flowchart,
            "FORMULAR": self._chunk_form,
            "PROZESS": self._chunk_process_document,
            "QUALITÄTSMANAGEMENT": self._chunk_quality_document,
            "COMPLIANCE": self._chunk_compliance_document
        }
        
        # Lade Prompt-Templates aus der Datenbank
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """Lädt Prompt-Templates aus der Datenbank für dokumenttyp-spezifische Strategien."""
        try:
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            result = db_session.execute(text('''
                SELECT pt.id, pt.name, pt.prompt_text, dt.name as document_type_name
                FROM prompt_templates pt
                JOIN document_types dt ON pt.document_type_id = dt.id
                WHERE pt.status = 'active'
                ORDER BY pt.id
            '''))
            
            self.prompt_templates = {}
            for template in result.fetchall():
                doc_type = template[3].upper()
                if doc_type not in self.prompt_templates:
                    self.prompt_templates[doc_type] = []
                
                self.prompt_templates[doc_type].append({
                    'id': template[0],
                    'name': template[1],
                    'prompt_text': template[2],
                    'document_type': doc_type
                })
            
            print(f"DEBUG: Geladene Prompt-Templates: {list(self.prompt_templates.keys())}")
            
        except Exception as e:
            print(f"DEBUG: Fehler beim Laden der Prompt-Templates: {e}")
            self.prompt_templates = {}
    
    def get_chunking_strategy_for_document_type(self, document_type: str) -> str:
        """
        Bestimmt die optimale Chunking-Strategie basierend auf dem Dokumenttyp
        und dem aktiven Standardprompt.
        
        WICHTIG: Die Strategie wird dynamisch aus dem Standard-Prompt extrahiert,
        um die JSON-Struktur zu erkennen, die von der Vision-AI verwendet wird.
        """
        doc_type_upper = document_type.upper()
        
        # Hole den aktiven Standardprompt für diesen Dokumenttyp
        active_prompt = self._get_active_standard_prompt(doc_type_upper)
        
        if active_prompt:
            print(f"DEBUG: Aktiver Standardprompt für {doc_type_upper}: {active_prompt['name']}")
            
            # Analysiere die Prompt-Struktur um die JSON-Struktur zu verstehen
            prompt_text = active_prompt['prompt_text']
            
            # WICHTIG: Prüfe auf verschiedene JSON-Strukturen DYNAMISCH aus dem Prompt
            # Die Vision-AI verwendet die Struktur, die im Prompt definiert ist!
            
            # 1. Flussdiagramm: "nodes" hat Priorität
            if '"nodes"' in prompt_text or "'nodes'" in prompt_text:
                print(f"DEBUG: Prompt verwendet nodes-Struktur (Flussdiagramm) - verwende _chunk_flowchart")
                return self._chunk_flowchart
            
            # 2. Arbeitsanweisung: "steps" mit "step_number"
            elif '"steps"' in prompt_text and '"step_number"' in prompt_text:
                print(f"DEBUG: Prompt verwendet steps-Struktur (Arbeitsanweisung) - verwende _chunk_work_instruction")
                return self._chunk_work_instruction
            
            # 3. SOP/Prozess: "process_steps" - für alle anderen (SOP, Prozess, Flussdiagramm mit process_steps)
            elif '"process_steps"' in prompt_text or "'process_steps'" in prompt_text:
                print(f"DEBUG: Prompt verwendet process_steps-Struktur - verwende _chunk_sop_document")
                # WICHTIG: _chunk_sop_document unterstützt jetzt beide Strukturen (pages und root-level)
                return self._chunk_sop_document
            
            # 4. Fallback: Generisches Chunking
            else:
                print(f"DEBUG: Prompt-Struktur nicht erkannt, verwende generisches Chunking")
                print(f"DEBUG: Prompt-Text-Snippet (erste 500 Zeichen): {prompt_text[:500]}")
                return self._chunk_generic_document
        else:
            print(f"DEBUG: Kein aktiver Standardprompt für {doc_type_upper} gefunden")
            return self._chunk_generic_document
    
    def _get_active_standard_prompt(self, document_type: str) -> Optional[Dict[str, Any]]:
        """
        Hole den aktiven Standardprompt für einen Dokumenttyp.
        """
        try:
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            result = db_session.execute(text('''
                SELECT pt.id, pt.name, pt.prompt_text, pt.status
                FROM prompt_templates pt
                JOIN document_types dt ON pt.document_type_id = dt.id
                WHERE dt.name = :doc_type 
                AND pt.status = 'active'
                ORDER BY pt.created_at DESC
                LIMIT 1
            '''), {"doc_type": document_type.title()})
            
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'prompt_text': row[2],
                    'status': row[3]
                }
            return None
            
        except Exception as e:
            print(f"DEBUG: Fehler beim Abrufen des aktiven Prompts: {e}")
            return None
    
    def create_chunks_from_vision_data(
        self,
        vision_data: Dict[str, Any],
        document_id: int,
        document_type: str = "SOP"
    ) -> List[DocumentChunk]:
        """
        Erstellt dokumenttyp-spezifische Chunks aus Vision-JSON-Daten.
        
        Nutzt die Prompt-Templates aus der Datenbank, um die optimale
        Chunking-Strategie für den Dokumenttyp zu bestimmen.
        
        Args:
            vision_data: Die Vision-AI-Ergebnisse im JSON-Format
            document_id: Die ID des Dokuments
            document_type: Der Dokumenttyp (SOP, ARBEITSANWEISUNG, etc.)
            
        Returns:
            Eine Liste von DocumentChunk-Entities
        """
        # Bestimme die optimale Chunking-Strategie basierend auf Prompt-Templates
        chunking_strategy = self.get_chunking_strategy_for_document_type(document_type)
        
        print(f"DEBUG: Verwende Chunking-Strategie für {document_type.upper()}")
        
        return chunking_strategy(vision_data, document_id)
    
    def _chunk_sop_document(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für SOP-Dokumente und Flussdiagramme mit process_steps."""
        chunks = []
        
        # WICHTIG: Vision-Daten können zwei Strukturen haben:
        # 1. {"pages": [{"page_number": 1, "content": {...}}]} (alte Struktur)
        # 2. {"document_metadata": ..., "process_steps": [...]} (neue Struktur - direkt im Root)
        
        if "pages" in vision_data:
            # Alte Struktur: Mehrere Pages
            for page in vision_data.get("pages", []):
                page_number = page.get("page_number", 1)
                content = page.get("content", {})
                
                # 1. Dokument-Metadaten als separaten Chunk
                if "document_metadata" in content:
                    metadata_chunk = self._create_metadata_chunk(
                        content["document_metadata"], document_id, page_number
                    )
                    chunks.append(metadata_chunk)
                
                # 2. Prozessschritte als separate Chunks
                if "process_steps" in content:
                    for step in content["process_steps"]:
                        step_chunk = self._create_process_step_chunk(
                            step, document_id, page_number
                        )
                        chunks.append(step_chunk)
                
                # 3. Compliance-Anforderungen als separaten Chunk
                if "compliance_requirements" in content:
                    compliance_chunk = self._create_compliance_chunk(
                        content["compliance_requirements"], document_id, page_number
                    )
                    chunks.append(compliance_chunk)
                
                # 4. Kritische Regeln als separate Chunks
                if "critical_rules" in content:
                    for rule in content["critical_rules"]:
                        rule_chunk = self._create_critical_rule_chunk(
                            rule, document_id, page_number
                        )
                        chunks.append(rule_chunk)
                
                # 5. Referenzierte Dokumente als separaten Chunk
                if "referenced_documents" in content:
                    ref_chunk = self._create_referenced_documents_chunk(
                        content["referenced_documents"], document_id, page_number
                    )
                    chunks.append(ref_chunk)
        else:
            # Neue Struktur: Direkt im Root-Level (kommt von _convert_to_vision_json)
            page_number = 1  # Default, könnte aus Vision-Daten extrahiert werden
            
            # 1. Dokument-Metadaten als separaten Chunk
            if "document_metadata" in vision_data:
                metadata_chunk = self._create_metadata_chunk(
                    vision_data["document_metadata"], document_id, page_number
                )
                chunks.append(metadata_chunk)
            
            # 2. Prozessschritte als separate Chunks
            if "process_steps" in vision_data:
                print(f"DEBUG: _chunk_sop_document: Gefunden {len(vision_data['process_steps'])} process_steps")
                for step in vision_data["process_steps"]:
                    step_chunk = self._create_process_step_chunk(
                        step, document_id, page_number
                    )
                    chunks.append(step_chunk)
            
            # 3. Compliance-Anforderungen als separaten Chunk
            if "compliance_requirements" in vision_data:
                compliance_chunk = self._create_compliance_chunk(
                    vision_data["compliance_requirements"], document_id, page_number
                )
                chunks.append(compliance_chunk)
            
            # 4. Kritische Regeln als separate Chunks
            if "critical_rules" in vision_data:
                for rule in vision_data["critical_rules"]:
                    rule_chunk = self._create_critical_rule_chunk(
                        rule, document_id, page_number
                    )
                    chunks.append(rule_chunk)
            
            # 5. Referenzierte Dokumente als separaten Chunk
            if "referenced_documents" in vision_data:
                ref_chunk = self._create_referenced_documents_chunk(
                    vision_data["referenced_documents"], document_id, page_number
                )
                chunks.append(ref_chunk)
            
            # 6. Definitions als separaten Chunk
            if "definitions" in vision_data:
                def_chunk = self._create_definitions_chunk(
                    vision_data["definitions"], document_id, page_number
                )
                chunks.append(def_chunk)
        
        print(f"DEBUG: _chunk_sop_document: Erstellt {len(chunks)} Chunks")
        return chunks
    
    def _chunk_work_instruction(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Arbeitsanweisungen."""
        print(f"DEBUG: _chunk_work_instruction aufgerufen mit document_id={document_id}")
        print(f"DEBUG: Vision data keys: {list(vision_data.keys())}")
        chunks = []
        
        # Prüfe ob es sich um die neue Vision-JSON-Struktur handelt
        if "steps" in vision_data:
            print(f"DEBUG: Neue Vision-JSON-Struktur erkannt, rufe _chunk_new_work_instruction_structure auf")
            return self._chunk_new_work_instruction_structure(vision_data, document_id)
        
        # Fallback für alte Struktur
        for page in vision_data.get("pages", []):
            page_number = page.get("page_number", 1)
            content = page.get("content", {})
            
            # 1. Titel und Beschreibung
            if "title" in content or "description" in content:
                title_chunk = self._create_title_chunk(
                    content, document_id, page_number
                )
                chunks.append(title_chunk)
            
            # 2. Arbeitsschritte als separate Chunks
            if "work_steps" in content:
                for step in content["work_steps"]:
                    step_chunk = self._create_work_step_chunk(
                        step, document_id, page_number
                    )
                    chunks.append(step_chunk)
            
            # 3. Sicherheitshinweise als separaten Chunk
            if "safety_instructions" in content:
                safety_chunk = self._create_safety_chunk(
                    content["safety_instructions"], document_id, page_number
                )
                chunks.append(safety_chunk)
            
            # 4. Benötigte Werkzeuge/Materialien
            if "required_tools" in content:
                tools_chunk = self._create_tools_chunk(
                    content["required_tools"], document_id, page_number
                )
                chunks.append(tools_chunk)
        
        return chunks
    
    def _chunk_new_work_instruction_structure(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking für neue Vision-JSON-Struktur (Arbeitsanweisungen)."""
        print(f"DEBUG: _chunk_new_work_instruction_structure aufgerufen mit document_id={document_id}")
        print(f"DEBUG: Vision data keys: {list(vision_data.keys())}")
        chunks = []
        
        # 1. Dokument-Metadaten Chunk
        if "document_metadata" in vision_data:
            doc_meta = vision_data["document_metadata"]
            meta_text = f"Dokument: {doc_meta.get('title', '')} (AA-ID: {doc_meta.get('aa_id', '')})\n"
            meta_text += f"Version: {doc_meta.get('version', '')}\n"
            meta_text += f"Erstellt von: {doc_meta.get('created_by', '')}\n"
            meta_text += f"Geprüft von: {doc_meta.get('reviewed_by', '')}\n"
            meta_text += f"Freigegeben von: {doc_meta.get('approved_by', '')}\n"
            meta_text += f"Organisation: {doc_meta.get('organization', '')}"
            
            meta_chunk = DocumentChunk(
                id=None,
                indexed_document_id=document_id,
                chunk_id=f"{document_id}_meta",
                chunk_text=meta_text,
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=["Dokument-Metadaten"],
                    chunk_type="metadata",
                    token_count=len(meta_text.split())
                ),
                qdrant_point_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            chunks.append(meta_chunk)
        
        # 2. Prozess-Übersicht Chunk
        if "process_overview" in vision_data:
            process = vision_data["process_overview"]
            process_text = f"Ziel: {process.get('goal', '')}\n"
            process_text += f"Bereich: {process.get('scope', '')}\n"
            
            if process.get("general_safety"):
                process_text += "Allgemeine Sicherheitshinweise:\n"
                for safety in process["general_safety"]:
                    process_text += f"- {safety.get('topic', '')}: {safety.get('instruction', '')}\n"
            
            process_chunk = DocumentChunk(
                id=None,
                indexed_document_id=document_id,
                chunk_id=f"{document_id}_process",
                chunk_text=process_text,
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=["Prozess-Übersicht"],
                    chunk_type="process_overview",
                    token_count=len(process_text.split())
                ),
                qdrant_point_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            chunks.append(process_chunk)
        
        # 3. Arbeitsschritte als separate Chunks
        if "steps" in vision_data:
            for i, step in enumerate(vision_data["steps"]):
                step_text = f"Schritt {step.get('step_number', i+1)}: {step.get('title', '')}\n"
                step_text += f"Beschreibung: {step.get('description', '')}\n"
                
                # Artikel hinzufügen
                if step.get("article_data"):
                    step_text += "Benötigte Artikel:\n"
                    for article in step["article_data"]:
                        step_text += f"- {article.get('name', '')} (Art-Nr: {article.get('art_nr', '')}) "
                        step_text += f"Menge: {article.get('qty_number', '')} {article.get('qty_unit', '')}\n"
                
                # Werkzeuge hinzufügen
                if step.get("tools"):
                    step_text += "Werkzeuge:\n"
                    for tool in step["tools"]:
                        step_text += f"- {tool.get('name', '')}\n"
                
                # Sicherheitshinweise hinzufügen
                if step.get("safety_instructions"):
                    step_text += "Sicherheitshinweise:\n"
                    for safety in step["safety_instructions"]:
                        step_text += f"- {safety.get('topic', '')}: {safety.get('instruction', '')}\n"
                
                # Qualitätsprüfungen hinzufügen
                if step.get("quality_checks"):
                    step_text += "Qualitätsprüfungen:\n"
                    for check in step["quality_checks"]:
                        step_text += f"- {check}\n"
                
                step_chunk = DocumentChunk(
                    id=None,
                    indexed_document_id=document_id,
                    chunk_id=f"{document_id}_step_{step.get('step_number', i+1)}",
                    chunk_text=step_text,
                    metadata=ChunkMetadata(
                        page_numbers=[vision_data.get("page_metadata", {}).get("page_number", 1)],
                        heading_hierarchy=[f"Schritt {step.get('step_number', i+1)}: {step.get('title', '')}"],
                        chunk_type="work_step",
                        token_count=len(step_text.split())
                    ),
                    qdrant_point_id=str(uuid.uuid4()),
                    created_at=datetime.now()
                )
                chunks.append(step_chunk)
        
        return chunks
    
    def _chunk_flowchart(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Flussdiagramme mit nodes-Struktur."""
        chunks = []
        
        # WICHTIG: Vision-Daten können zwei Strukturen haben:
        # 1. {"pages": [{"page_number": 1, "content": {...}}]} (alte Struktur)
        # 2. {"nodes": [...], "connections": [...]} (neue Struktur - direkt im Root)
        
        if "pages" in vision_data:
            # Alte Struktur: Mehrere Pages
            for page in vision_data.get("pages", []):
                page_number = page.get("page_number", 1)
                content = page.get("content", {})
                
                # 1. Diagramm-Übersicht
                if "diagram_overview" in content:
                    overview_chunk = self._create_diagram_overview_chunk(
                        content["diagram_overview"], document_id, page_number
                    )
                    chunks.append(overview_chunk)
                
                # 2. Knoten als separate Chunks
                if "nodes" in content:
                    for node in content["nodes"]:
                        node_chunk = self._create_node_chunk(
                            node, document_id, page_number
                        )
                        chunks.append(node_chunk)
                
                # 3. Entscheidungspunkte als separate Chunks
                if "decision_points" in content:
                    for decision in content["decision_points"]:
                        decision_chunk = self._create_decision_chunk(
                            decision, document_id, page_number
                        )
                        chunks.append(decision_chunk)
                
                # 4. Verbindungen/Flüsse
                if "connections" in content:
                    connections_chunk = self._create_connections_chunk(
                        content["connections"], document_id, page_number
                    )
                    chunks.append(connections_chunk)
        else:
            # Neue Struktur: Direkt im Root-Level (kommt von _convert_to_vision_json)
            page_number = 1  # Default
            
            # 1. Diagramm-Übersicht
            if "diagram_overview" in vision_data:
                overview_chunk = self._create_diagram_overview_chunk(
                    vision_data["diagram_overview"], document_id, page_number
                )
                chunks.append(overview_chunk)
            
            # 2. Knoten als separate Chunks
            if "nodes" in vision_data:
                print(f"DEBUG: _chunk_flowchart: Gefunden {len(vision_data['nodes'])} nodes")
                for node in vision_data["nodes"]:
                    node_chunk = self._create_node_chunk(
                        node, document_id, page_number
                    )
                    chunks.append(node_chunk)
            
            # 3. Entscheidungspunkte als separate Chunks
            if "decision_points" in vision_data:
                for decision in vision_data["decision_points"]:
                    decision_chunk = self._create_decision_chunk(
                        decision, document_id, page_number
                    )
                    chunks.append(decision_chunk)
            
            # 4. Verbindungen/Flüsse
            if "connections" in vision_data:
                connections_chunk = self._create_connections_chunk(
                    vision_data["connections"], document_id, page_number
                )
                chunks.append(connections_chunk)
            
            # 5. Dokument-Metadaten (falls vorhanden)
            if "document_metadata" in vision_data:
                metadata_chunk = self._create_metadata_chunk(
                    vision_data["document_metadata"], document_id, page_number
                )
                chunks.append(metadata_chunk)
        
        print(f"DEBUG: _chunk_flowchart: Erstellt {len(chunks)} Chunks")
        return chunks
    
    def _chunk_form(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Formulare."""
        chunks = []
        
        for page in vision_data.get("pages", []):
            page_number = page.get("page_number", 1)
            content = page.get("content", {})
            
            # 1. Formular-Header
            if "form_header" in content:
                header_chunk = self._create_form_header_chunk(
                    content["form_header"], document_id, page_number
                )
                chunks.append(header_chunk)
            
            # 2. Felder als separate Chunks
            if "fields" in content:
                for field in content["fields"]:
                    field_chunk = self._create_field_chunk(
                        field, document_id, page_number
                    )
                    chunks.append(field_chunk)
            
            # 3. Validierungsregeln
            if "validation_rules" in content:
                validation_chunk = self._create_validation_chunk(
                    content["validation_rules"], document_id, page_number
                )
                chunks.append(validation_chunk)
        
        return chunks
    
    def _chunk_process_document(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Prozessdokumente."""
        return self._chunk_sop_document(vision_data, document_id)  # Ähnlich wie SOP
    
    def _chunk_quality_document(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Qualitätsmanagement-Dokumente."""
        chunks = []
        
        for page in vision_data.get("pages", []):
            page_number = page.get("page_number", 1)
            content = page.get("content", {})
            
            # 1. Qualitätsziele
            if "quality_objectives" in content:
                objectives_chunk = self._create_quality_objectives_chunk(
                    content["quality_objectives"], document_id, page_number
                )
                chunks.append(objectives_chunk)
            
            # 2. Messverfahren
            if "measurement_procedures" in content:
                for procedure in content["measurement_procedures"]:
                    procedure_chunk = self._create_measurement_procedure_chunk(
                        procedure, document_id, page_number
                    )
                    chunks.append(procedure_chunk)
            
            # 3. Qualitätskriterien
            if "quality_criteria" in content:
                criteria_chunk = self._create_quality_criteria_chunk(
                    content["quality_criteria"], document_id, page_number
                )
                chunks.append(criteria_chunk)
        
        return chunks
    
    def _chunk_compliance_document(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Chunking-Strategie für Compliance-Dokumente."""
        chunks = []
        
        for page in vision_data.get("pages", []):
            page_number = page.get("page_number", 1)
            content = page.get("content", {})
            
            # 1. Compliance-Standards
            if "compliance_standards" in content:
                standards_chunk = self._create_compliance_standards_chunk(
                    content["compliance_standards"], document_id, page_number
                )
                chunks.append(standards_chunk)
            
            # 2. Anforderungen als separate Chunks
            if "requirements" in content:
                for requirement in content["requirements"]:
                    req_chunk = self._create_requirement_chunk(
                        requirement, document_id, page_number
                    )
                    chunks.append(req_chunk)
            
            # 3. Audit-Kriterien
            if "audit_criteria" in content:
                audit_chunk = self._create_audit_criteria_chunk(
                    content["audit_criteria"], document_id, page_number
                )
                chunks.append(audit_chunk)
        
        return chunks
    
    def _chunk_generic_document(self, vision_data: Dict[str, Any], document_id: int) -> List[DocumentChunk]:
        """Fallback-Chunking-Strategie für unbekannte Dokumenttypen."""
        chunks = []
        
        for page in vision_data.get("pages", []):
            page_number = page.get("page_number", 1)
            content = page.get("content", {})
            
            # Einfache Text-Chunking
            if "text" in content:
                text_chunk = self._create_simple_text_chunk(
                    content["text"], document_id, page_number
                )
                chunks.append(text_chunk)
            
            # Tabellen-Chunking
            if "tables" in content:
                for table in content["tables"]:
                    table_chunk = self._create_table_chunk(
                        table, document_id, page_number
                    )
                    chunks.append(table_chunk)
        
        return chunks
    
    # ===== CHUNK-ERSTELLUNGSMETHODEN =====
    
    def _create_metadata_chunk(self, metadata: Dict[str, Any], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen Metadaten-Chunk."""
        chunk_text = f"Dokument: {metadata.get('title', 'Unbekannt')}\n"
        chunk_text += f"Typ: {metadata.get('document_type', 'Unbekannt')}\n"
        chunk_text += f"Version: {metadata.get('version', 'Unbekannt')}\n"
        chunk_text += f"Organisation: {metadata.get('organization', 'Unbekannt')}\n"
        chunk_text += f"Erstellt von: {metadata.get('created_by', {}).get('name', 'Unbekannt')}\n"
        chunk_text += f"Geprüft von: {metadata.get('reviewed_by', {}).get('name', 'Unbekannt')}\n"
        chunk_text += f"Genehmigt von: {metadata.get('approved_by', {}).get('name', 'Unbekannt')}"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_metadata",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Dokument-Metadaten"],
                chunk_type="metadata",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_process_step_chunk(self, step: Dict[str, Any], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen Prozessschritt-Chunk."""
        step_number = step.get('step_number', 'Unbekannt')
        label = step.get('label', 'Unbekannt')
        description = step.get('description', 'Keine Beschreibung')
        
        chunk_text = f"Schritt {step_number}: {label}\n"
        chunk_text += f"Beschreibung: {description}\n"
        
        # Verantwortliche Abteilung
        if 'responsible_department' in step:
            dept = step['responsible_department']
            chunk_text += f"Verantwortlich: {dept.get('short', '')} - {dept.get('long', '')}\n"
        
        # Inputs/Outputs
        if 'inputs' in step:
            chunk_text += f"Eingaben: {', '.join(step['inputs'])}\n"
        if 'outputs' in step:
            chunk_text += f"Ausgaben: {', '.join(step['outputs'])}\n"
        
        # Entscheidungen
        if 'decision' in step and step['decision'].get('is_decision', False):
            decision = step['decision']
            chunk_text += f"Entscheidung: {decision.get('question', '')}\n"
            chunk_text += f"Ja: {decision.get('yes_action', '')}\n"
            chunk_text += f"Nein: {decision.get('no_action', '')}\n"
        
        # Notizen
        if 'notes' in step:
            chunk_text += f"Notizen: {'; '.join(step['notes'])}\n"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_step_{step_number}",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=[f"Schritt {step_number}", label],
                chunk_type="process_step",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_compliance_chunk(self, compliance: List[Dict[str, Any]], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen Compliance-Chunk."""
        chunk_text = "Compliance-Anforderungen:\n"
        for req in compliance:
            standard = req.get('standard', 'Unbekannt')
            section = req.get('section', 'Unbekannt')
            requirement = req.get('requirement', 'Keine Anforderung')
            chunk_text += f"- {standard} ({section}): {requirement}\n"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_compliance",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Compliance-Anforderungen"],
                chunk_type="compliance",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_critical_rule_chunk(self, rule: Dict[str, Any], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen kritischen Regel-Chunk."""
        rule_text = rule.get('rule', 'Keine Regel')
        consequence = rule.get('consequence', 'Keine Konsequenz')
        linked_step = rule.get('linked_process_step', 'Kein Schritt')
        
        chunk_text = f"Kritische Regel: {rule_text}\n"
        chunk_text += f"Konsequenz: {consequence}\n"
        chunk_text += f"Verlinkter Schritt: {linked_step}"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_rule_{linked_step}",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Kritische Regeln", f"Schritt {linked_step}"],
                chunk_type="critical_rule",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_referenced_documents_chunk(self, refs: List[Dict[str, Any]], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen referenzierte Dokumente-Chunk."""
        chunk_text = "Referenzierte Dokumente:\n"
        for ref in refs:
            doc_type = ref.get('type', 'Unbekannt')
            reference = ref.get('reference', 'Unbekannt')
            title = ref.get('title', 'Unbekannt')
            version = ref.get('version', 'Unbekannt')
            chunk_text += f"- {doc_type}: {reference} - {title} (Version: {version})\n"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_references",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Referenzierte Dokumente"],
                chunk_type="references",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_definitions_chunk(self, definitions: List[Dict[str, Any]], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen Definitions-Chunk."""
        chunk_text = "Definitionen:\n"
        for def_item in definitions:
            term = def_item.get('term', 'Unbekannt')
            definition = def_item.get('definition', 'Keine Definition')
            chunk_text += f"- {term}: {definition}\n"
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_definitions",
            chunk_text=chunk_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Definitionen"],
                chunk_type="definitions",
                token_count=self._estimate_tokens(chunk_text),
                sentence_count=len(chunk_text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_simple_text_chunk(self, text: str, document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen einfachen Text-Chunk."""
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_text",
            chunk_text=text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Text"],
                chunk_type="text",
                token_count=self._estimate_tokens(text),
                sentence_count=len(text.split('.')),
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _create_table_chunk(self, table: Dict[str, Any], document_id: int, page_number: int) -> DocumentChunk:
        """Erstellt einen Tabellen-Chunk."""
        table_text = self._table_to_text(table.get("data", []))
        
        return DocumentChunk(
            id=None,
            indexed_document_id=document_id,
            chunk_id=f"doc_{document_id}_page_{page_number}_table",
            chunk_text=table_text,
            metadata=ChunkMetadata(
                page_numbers=[page_number],
                heading_hierarchy=["Tabelle"],
                chunk_type="table",
                token_count=self._estimate_tokens(table_text),
                sentence_count=1,
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Schätzt die Token-Anzahl eines Textes."""
        return len(text) // 4
    
    def _table_to_text(self, table_data: List[List[str]]) -> str:
        """Konvertiert Tabellendaten in einen lesbaren Text."""
        if not table_data:
            return ""
        
        header = table_data[0]
        rows = table_data[1:]
        
        table_str = "Tabelle:\n"
        table_str += " | ".join(header) + "\n"
        table_str += "---" * len(header) + "\n"
        for row in rows:
            table_str += " | ".join(row) + "\n"
        return table_str


class StructuredChunkingService:
    """
    Service für strukturierte Chunking-Strategie.
    
    Verarbeitet Vision-JSON-Daten und erstellt semantisch sinnvolle Chunks
    für spezifische Fragen wie "Welche Artikelnummer hat die Freilaufwelle?".
    """
    
    def __init__(self):
        """Initialisiert den strukturierten Chunking Service."""
        self.article_number_pattern = re.compile(r'\b\d{3}\.\d{3}\.\d{3}\b')
        self.heading_pattern = re.compile(r'^(\d+\.?\s*[A-ZÄÖÜ][^\n]*)$', re.MULTILINE)
        self.section_pattern = re.compile(r'^(\d+\.?\s*[A-ZÄÖÜ][^\n]*)$', re.MULTILINE)
    
    def create_chunks_from_vision_data(
        self, 
        vision_data: Dict[str, Any], 
        document_id: int
    ) -> List[DocumentChunk]:
        """
        Erstelle strukturierte Chunks aus Vision-JSON-Daten.
        
        Args:
            vision_data: Vision-JSON-Daten vom Upload
            document_id: Dokument-ID
            
        Returns:
            Liste von strukturierten DocumentChunk-Objekten
        """
        chunks = []
        
        if "pages" not in vision_data:
            return chunks
        
        for page_data in vision_data["pages"]:
            page_number = page_data.get("page_number", 1)
            content = page_data.get("content", {})
            
            # Erstelle verschiedene Chunk-Typen
            chunks.extend(self._create_text_chunks(content, document_id, page_number))
            chunks.extend(self._create_table_chunks(content, document_id, page_number))
            chunks.extend(self._create_image_chunks(content, document_id, page_number))
        
        return chunks
    
    def _create_text_chunks(
        self, 
        content: Dict[str, Any], 
        document_id: int, 
        page_number: int
    ) -> List[DocumentChunk]:
        """Erstelle Text-Chunks mit hierarchischer Struktur."""
        chunks = []
        text = content.get("text", "")
        
        if not text.strip():
            return chunks
        
        # Erkenne Überschriften und erstelle hierarchische Chunks
        sections = self._split_into_sections(text)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            # Extrahiere Überschriften
            headings = self._extract_headings(section)
            
            # Erstelle Chunk
            chunk_id = f"doc_{document_id}_page_{page_number}_text_{i}"
            
            chunk = DocumentChunk(
                id=None,
                indexed_document_id=document_id,
                chunk_id=chunk_id,
                chunk_text=section.strip(),
                metadata=ChunkMetadata(
                    page_numbers=[page_number],
                    heading_hierarchy=headings,
                    chunk_type="text",
                    token_count=self._estimate_tokens(section),
                    sentence_count=len(section.split('.')),
                    has_overlap=False,
                    overlap_sentence_count=0
                ),
                qdrant_point_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_table_chunks(
        self, 
        content: Dict[str, Any], 
        document_id: int, 
        page_number: int
    ) -> List[DocumentChunk]:
        """Erstelle Tabellen-Chunks."""
        chunks = []
        tables = content.get("tables", [])
        
        for i, table in enumerate(tables):
            if not table.get("data"):
                continue
            
            # Konvertiere Tabelle zu Text
            table_text = self._table_to_text(table["data"])
            
            # Erstelle Chunk
            chunk_id = f"doc_{document_id}_page_{page_number}_table_{i}"
            
            chunk = DocumentChunk(
                id=None,
                indexed_document_id=document_id,
                chunk_id=chunk_id,
                chunk_text=table_text,
                metadata=ChunkMetadata(
                    page_numbers=[page_number],
                    heading_hierarchy=["Tabelle"],
                    chunk_type="table",
                    token_count=self._estimate_tokens(table_text),
                    sentence_count=1,
                    has_overlap=False,
                    overlap_sentence_count=0
                ),
                qdrant_point_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_image_chunks(
        self, 
        content: Dict[str, Any], 
        document_id: int, 
        page_number: int
    ) -> List[DocumentChunk]:
        """Erstelle Bild-Chunks."""
        chunks = []
        images = content.get("images", [])
        
        for i, image in enumerate(images):
            if not image.get("description") and not image.get("ocr_text"):
                continue
            
            # Kombiniere Beschreibung und OCR-Text
            image_text = f"{image.get('description', '')} {image.get('ocr_text', '')}".strip()
            
            if not image_text:
                continue
            
            # Erstelle Chunk
            chunk_id = f"doc_{document_id}_page_{page_number}_image_{i}"
            
            chunk = DocumentChunk(
                id=None,
                indexed_document_id=document_id,
                chunk_id=chunk_id,
                chunk_text=image_text,
                metadata=ChunkMetadata(
                    page_numbers=[page_number],
                    heading_hierarchy=["Bild"],
                    chunk_type="image",
                    token_count=self._estimate_tokens(image_text),
                    sentence_count=1,
                    has_overlap=False,
                    overlap_sentence_count=0
                ),
                qdrant_point_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Teile Text in semantische Abschnitte."""
        # Erkenne Überschriften und teile danach
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Prüfe ob es eine Überschrift ist
            if self.heading_pattern.match(line):
                # Speichere vorherigen Abschnitt
                if current_section.strip():
                    sections.append(current_section.strip())
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        # Füge letzten Abschnitt hinzu
        if current_section.strip():
            sections.append(current_section.strip())
        
        # Falls keine Überschriften gefunden, teile nach Absätzen
        if not sections:
            sections = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        return sections
    
    def _extract_headings(self, text: str) -> List[str]:
        """Extrahiere Überschriften aus Text."""
        headings = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if self.heading_pattern.match(line):
                headings.append(line)
        
        return headings
    
    def _table_to_text(self, table_data: List[List[str]]) -> str:
        """Konvertiere Tabellendaten zu Text."""
        if not table_data:
            return ""
        
        text_parts = []
        
        # Header
        if table_data:
            header = " | ".join(table_data[0])
            text_parts.append(f"Tabelle: {header}")
        
        # Datenzeilen
        for row in table_data[1:]:
            row_text = " | ".join(row)
            text_parts.append(row_text)
        
        return "\n".join(text_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Schätze Token-Anzahl (ca. 4 Zeichen pro Token)."""
        return max(1, len(text) // 4)
    
    def extract_article_numbers(self, text: str) -> List[str]:
        """Extrahiere Artikelnummern aus Text."""
        return self.article_number_pattern.findall(text)
    
    def create_specific_chunks_for_question(
        self, 
        question: str, 
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """
        Erstelle spezifische Chunks basierend auf einer Frage.
        
        Für Fragen wie "Welche Artikelnummer hat die Freilaufwelle?"
        werden relevante Chunks gefiltert und priorisiert.
        """
        relevant_chunks = []
        
        # Normalisiere Frage
        question_lower = question.lower()
        
        for chunk in chunks:
            chunk_text_lower = chunk.chunk_text.lower()
            relevance_score = 0.0
            
            # Prüfe verschiedene Relevanz-Kriterien
            if "artikelnummer" in question_lower and "artikelnummer" in chunk_text_lower:
                relevance_score += 0.3
            
            if "freilaufwelle" in question_lower and "freilaufwelle" in chunk_text_lower:
                relevance_score += 0.3
            
            # Prüfe auf Artikelnummern im Chunk
            article_numbers = self.extract_article_numbers(chunk.chunk_text)
            if article_numbers:
                relevance_score += 0.2
            
            # Prüfe Chunk-Typ
            if chunk.metadata.chunk_type == "table":
                relevance_score += 0.1  # Tabellen haben oft Artikelnummern
            
            if chunk.metadata.chunk_type == "image":
                relevance_score += 0.1  # Bilder können Artikelnummern enthalten
            
            # Füge Chunk hinzu wenn relevant
            if relevance_score > 0.1:
                # Aktualisiere Relevanz-Score
                chunk.source_references[0].relevance_score = min(1.0, relevance_score)
                relevant_chunks.append(chunk)
        
        # Sortiere nach Relevanz
        relevant_chunks.sort(
            key=lambda c: c.source_references[0].relevance_score, 
            reverse=True
        )
        
        return relevant_chunks