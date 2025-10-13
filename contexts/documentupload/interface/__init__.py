"""
Interface Layer für Document Upload Context

Dieser Layer enthält die FastAPI Router und Schemas für die HTTP API.
"""

from .router import router
from .schemas import (
    # Request Schemas
    UploadDocumentRequest,
    AssignInterestGroupsRequest,
    
    # Response Schemas
    UploadDocumentResponse,
    GeneratePreviewResponse,
    AssignInterestGroupsResponse,
    GetUploadDetailsResponse,
    GetUploadsListResponse,
    DeleteUploadResponse,
    ErrorResponse,
    
    # Entity Schemas
    UploadedDocumentSchema,
    UploadedDocumentDetailSchema,
    DocumentPageSchema,
    InterestGroupAssignmentSchema,
)

__all__ = [
    # Router
    'router',
    
    # Request Schemas
    'UploadDocumentRequest',
    'AssignInterestGroupsRequest',
    
    # Response Schemas
    'UploadDocumentResponse',
    'GeneratePreviewResponse',
    'AssignInterestGroupsResponse',
    'GetUploadDetailsResponse',
    'GetUploadsListResponse',
    'DeleteUploadResponse',
    'ErrorResponse',
    
    # Entity Schemas
    'UploadedDocumentSchema',
    'UploadedDocumentDetailSchema',
    'DocumentPageSchema',
    'InterestGroupAssignmentSchema',
]

