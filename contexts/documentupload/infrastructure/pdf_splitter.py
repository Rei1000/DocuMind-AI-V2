"""
PDF Splitter Service für Document Upload Context

Verantwortlich für das Aufteilen mehrseitiger PDFs in Einzelseiten
und die Konvertierung zu Bildern.
"""

import io
from pathlib import Path
from typing import List, BinaryIO
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image


class PDFSplitterService:
    """
    PDF Splitter Service.
    
    Features:
    - Split PDF in Einzelseiten
    - Konvertiere PDF-Seiten zu Bildern (JPG)
    - Unterstützung für große PDFs (Memory-efficient)
    
    Args:
        dpi: DPI für Image-Konvertierung (default: 200)
    """
    
    def __init__(self, dpi: int = 200):
        self.dpi = dpi
    
    async def get_page_count(self, pdf_path: str) -> int:
        """
        Ermittle Anzahl Seiten in PDF.
        
        Args:
            pdf_path: Pfad zum PDF
            
        Returns:
            Anzahl Seiten
            
        Raises:
            ValueError: Wenn PDF ungültig
        """
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            raise ValueError(f"Invalid PDF: {e}")
    
    async def split_pdf_to_images(
        self,
        pdf_path: str,
        output_format: str = 'JPEG'
    ) -> List[Image.Image]:
        """
        Konvertiere PDF-Seiten zu Bildern.
        
        Args:
            pdf_path: Pfad zum PDF
            output_format: Bildformat (JPEG, PNG)
            
        Returns:
            Liste von PIL Images (eine pro Seite)
            
        Raises:
            ValueError: Wenn PDF ungültig
            IOError: Bei Konvertierungs-Fehler
        """
        try:
            # Konvertiere PDF zu Bildern
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt=output_format.lower()
            )
            return images
        except Exception as e:
            raise IOError(f"Failed to convert PDF to images: {e}")
    
    async def split_pdf_to_bytes(
        self,
        pdf_bytes: bytes,
        output_format: str = 'JPEG'
    ) -> List[Image.Image]:
        """
        Konvertiere PDF-Bytes zu Bildern.
        
        Args:
            pdf_bytes: PDF als Bytes
            output_format: Bildformat (JPEG, PNG)
            
        Returns:
            Liste von PIL Images
        """
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                fmt=output_format.lower()
            )
            return images
        except Exception as e:
            raise IOError(f"Failed to convert PDF bytes to images: {e}")
    
    async def extract_single_page(
        self,
        pdf_path: str,
        page_number: int
    ) -> bytes:
        """
        Extrahiere einzelne PDF-Seite als neues PDF.
        
        Args:
            pdf_path: Pfad zum PDF
            page_number: Seitennummer (1-basiert)
            
        Returns:
            PDF-Bytes der einzelnen Seite
            
        Raises:
            ValueError: Wenn Seite nicht existiert
        """
        try:
            reader = PdfReader(pdf_path)
            
            if page_number < 1 or page_number > len(reader.pages):
                raise ValueError(f"Page {page_number} out of range (1-{len(reader.pages)})")
            
            # Erstelle neues PDF mit nur einer Seite
            writer = PdfWriter()
            writer.add_page(reader.pages[page_number - 1])  # 0-basiert
            
            # Schreibe zu Bytes
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            raise IOError(f"Failed to extract page: {e}")
    
    async def get_page_dimensions(
        self,
        pdf_path: str,
        page_number: int
    ) -> tuple[int, int]:
        """
        Ermittle Dimensionen einer PDF-Seite.
        
        Args:
            pdf_path: Pfad zum PDF
            page_number: Seitennummer (1-basiert)
            
        Returns:
            Tuple (width, height) in Pixel (bei self.dpi)
            
        Raises:
            ValueError: Wenn Seite nicht existiert
        """
        try:
            reader = PdfReader(pdf_path)
            
            if page_number < 1 or page_number > len(reader.pages):
                raise ValueError(f"Page {page_number} out of range")
            
            page = reader.pages[page_number - 1]
            
            # PDF-Punkte zu Pixel (1 Punkt = 1/72 Zoll)
            width_pt = float(page.mediabox.width)
            height_pt = float(page.mediabox.height)
            
            # Konvertiere zu Pixel bei gegebenem DPI
            width_px = int(width_pt * self.dpi / 72)
            height_px = int(height_pt * self.dpi / 72)
            
            return (width_px, height_px)
        except Exception as e:
            raise IOError(f"Failed to get page dimensions: {e}")

