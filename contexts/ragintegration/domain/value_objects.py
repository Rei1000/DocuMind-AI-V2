"""
RAG Integration Value Objects

Domain Value Objects für RAG Integration Context.
Basierend auf RAG-Anything Best Practices für moderne RAG-Konfiguration.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ParserType(Enum):
    """Verfügbare Parser basierend auf RAG-Anything."""
    MINERU = "mineru"
    DOCLING = "docling"


class ChunkingStrategy(Enum):
    """Chunking-Strategien basierend auf RAG-Anything."""
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    FIXED_SIZE = "fixed_size"
    STRUCTURED = "structured"


class EmbeddingModel(Enum):
    """Verfügbare Embedding-Modelle."""
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class AIModel(Enum):
    """Verfügbare AI-Modelle."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5_MINI = "gpt-5-mini"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"


@dataclass
class RAGConfig:
    """
    RAG-Konfiguration basierend auf RAG-Anything Best Practices.
    
    Diese Klasse definiert alle konfigurierbaren Parameter für das RAG-System:
    - Parser-Auswahl (MinerU vs Docling)
    - Chunking-Strategie (Semantic, Hierarchical, etc.)
    - Embedding-Modell
    - AI-Modell
    - Chunk-Parameter
    """
    
    # Parser-Konfiguration
    parser: str = ParserType.MINERU.value
    parse_method: str = "auto"  # auto, ocr, txt
    
    # Chunking-Konfiguration
    chunking_strategy: str = ChunkingStrategy.SEMANTIC.value
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Embedding-Konfiguration
    embedding_model: str = EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value
    
    # AI-Modell-Konfiguration
    ai_model: str = AIModel.GPT_4O_MINI.value
    
    # Kontext-Management
    max_context_chunks: int = 5
    context_window_size: int = 4000
    
    # Erweiterte Optionen
    enable_multimodal: bool = True
    enable_table_extraction: bool = True
    enable_formula_parsing: bool = True
    
    def __post_init__(self):
        """Validiere Konfiguration nach Initialisierung."""
        self._validate_config()
    
    def _validate_config(self):
        """Validiere alle Konfigurationsparameter."""
        # Parser validieren
        if self.parser not in [p.value for p in ParserType]:
            raise ValueError(f"Invalid parser: {self.parser}. Must be one of {[p.value for p in ParserType]}")
        
        # Chunking-Strategie validieren
        if self.chunking_strategy not in [s.value for s in ChunkingStrategy]:
            raise ValueError(f"Invalid chunking strategy: {self.chunking_strategy}. Must be one of {[s.value for s in ChunkingStrategy]}")
        
        # Embedding-Modell validieren
        if self.embedding_model not in [m.value for m in EmbeddingModel]:
            raise ValueError(f"Invalid embedding model: {self.embedding_model}. Must be one of {[m.value for m in EmbeddingModel]}")
        
        # AI-Modell validieren
        if self.ai_model not in [m.value for m in AIModel]:
            raise ValueError(f"Invalid AI model: {self.ai_model}. Must be one of {[m.value for m in AIModel]}")
        
        # Numerische Parameter validieren
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        
        if self.max_context_chunks <= 0:
            raise ValueError("max_context_chunks must be positive")
        
        if self.context_window_size <= 0:
            raise ValueError("context_window_size must be positive")
    
    def to_dict(self) -> dict:
        """Konvertiere Konfiguration zu Dictionary."""
        return {
            "parser": self.parser,
            "parse_method": self.parse_method,
            "chunking_strategy": self.chunking_strategy,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model,
            "ai_model": self.ai_model,
            "max_context_chunks": self.max_context_chunks,
            "context_window_size": self.context_window_size,
            "enable_multimodal": self.enable_multimodal,
            "enable_table_extraction": self.enable_table_extraction,
            "enable_formula_parsing": self.enable_formula_parsing
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RAGConfig':
        """Erstelle Konfiguration aus Dictionary."""
        return cls(**data)
    
    def get_available_options(self) -> dict:
        """Gibt alle verfügbaren Optionen zurück."""
        return {
            "parsers": [p.value for p in ParserType],
            "chunking_strategies": [s.value for s in ChunkingStrategy],
            "embedding_models": [m.value for m in EmbeddingModel],
            "ai_models": [m.value for m in AIModel],
            "parse_methods": ["auto", "ocr", "txt"]
        }


# ===== BESTEHENDE VALUE OBJECTS =====

@dataclass
class EmbeddingVector:
    """Embedding Vector Value Object."""
    vector: List[float]
    model: str
    dimensions: int
    
    def __post_init__(self):
        if len(self.vector) != self.dimensions:
            raise ValueError(f"Vector length {len(self.vector)} != dimensions {self.dimensions}")


@dataclass
class ChunkMetadata:
    """Chunk Metadata Value Object."""
    page_numbers: List[int]
    heading_hierarchy: List[str]
    chunk_type: str
    token_count: Optional[int] = None
    sentence_count: Optional[int] = None
    has_overlap: bool = False
    overlap_sentence_count: int = 0
    
    def __post_init__(self):
        if not self.page_numbers:
            raise ValueError("page_numbers cannot be empty")
        if not self.chunk_type:
            raise ValueError("chunk_type cannot be empty")


@dataclass
class SourceReference:
    """Source Reference Value Object."""
    document_id: int
    page_number: int
    chunk_id: str
    relevance_score: float
    
    def __post_init__(self):
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("relevance_score must be between 0.0 and 1.0")


class ChatMessageType(Enum):
    """Chat Message Types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"