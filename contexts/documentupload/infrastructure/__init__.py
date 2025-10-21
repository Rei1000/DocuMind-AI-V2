"""
Infrastructure Layer für Document Upload Context

Dieser Layer enthält alle technischen Implementierungen:
- File Storage (LocalFileStorageService)
- PDF Splitter (PDFSplitterService)
- Image Processor (ImageProcessorService)
- SQLAlchemy Repositories (Adapters)
- Mappers (DTO ↔ Entity)
"""

from .file_storage import LocalFileStorageService
from .pdf_splitter import PDFSplitterService
from .image_processor import ImageProcessorService
from .repositories import (
    SQLAlchemyUploadRepository,
    SQLAlchemyDocumentPageRepository,
    SQLAlchemyInterestGroupAssignmentRepository
)
from .mappers import (
    UploadDocumentMapper,
    DocumentPageMapper,
    InterestGroupAssignmentMapper
)

__all__ = [
    # File Storage
    'LocalFileStorageService',
    
    # Document Processing
    'PDFSplitterService',
    'ImageProcessorService',
    
    # Repositories (Adapters)
    'SQLAlchemyUploadRepository',
    'SQLAlchemyDocumentPageRepository',
    'SQLAlchemyInterestGroupAssignmentRepository',
    
    # Mappers
    'UploadDocumentMapper',
    'DocumentPageMapper',
    'InterestGroupAssignmentMapper',
]

