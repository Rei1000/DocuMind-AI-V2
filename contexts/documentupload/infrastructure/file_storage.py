"""
File Storage Service für Document Upload Context

Verantwortlich für das Speichern und Laden von Dateien im lokalen Filesystem.
"""

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime


class LocalFileStorageService:
    """
    Lokaler File Storage Service.
    
    Speichert Dateien in strukturierter Verzeichnis-Hierarchie:
    - /data/uploads/documents/YYYY/MM/DD/filename
    - /data/uploads/previews/YYYY/MM/DD/doc_id_page_1.jpg
    - /data/uploads/thumbnails/YYYY/MM/DD/doc_id_page_1_thumb.jpg
    
    Args:
        base_path: Basis-Pfad für Uploads (default: data/uploads)
    """
    
    def __init__(self, base_path: str = "data/uploads"):
        self.base_path = Path(base_path)
        self.documents_path = self.base_path / "documents"
        self.previews_path = self.base_path / "previews"
        self.thumbnails_path = self.base_path / "thumbnails"
        
        # Erstelle Verzeichnisse falls nicht vorhanden
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Erstelle Verzeichnis-Struktur."""
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.previews_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
    
    def _get_date_path(self) -> Path:
        """
        Generiere Datums-basierte Pfad-Struktur.
        
        Returns:
            Path: YYYY/MM/DD
        """
        now = datetime.utcnow()
        return Path(str(now.year)) / f"{now.month:02d}" / f"{now.day:02d}"
    
    async def save_document(
        self,
        file: BinaryIO,
        filename: str
    ) -> str:
        """
        Speichere Original-Dokument.
        
        Args:
            file: File-like Object (Binary)
            filename: Dateiname
            
        Returns:
            Relativer Pfad zur gespeicherten Datei
            
        Raises:
            IOError: Bei Speicher-Fehler
        """
        # Erstelle Datums-Pfad
        date_path = self._get_date_path()
        target_dir = self.documents_path / date_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Ziel-Pfad
        target_path = target_dir / filename
        
        # Speichere Datei
        try:
            with open(target_path, 'wb') as f:
                shutil.copyfileobj(file, f)
        except Exception as e:
            raise IOError(f"Failed to save document: {e}")
        
        # Returniere relativen Pfad
        return str(target_path.relative_to(self.base_path))
    
    async def save_preview(
        self,
        file: BinaryIO,
        document_id: int,
        page_number: int
    ) -> str:
        """
        Speichere Preview-Bild.
        
        Args:
            file: File-like Object (Binary)
            document_id: Dokument ID
            page_number: Seitennummer
            
        Returns:
            Relativer Pfad zum gespeicherten Preview
        """
        date_path = self._get_date_path()
        target_dir = self.previews_path / date_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"doc_{document_id}_page_{page_number}.jpg"
        target_path = target_dir / filename
        
        try:
            with open(target_path, 'wb') as f:
                shutil.copyfileobj(file, f)
        except Exception as e:
            raise IOError(f"Failed to save preview: {e}")
        
        return str(target_path.relative_to(self.base_path))
    
    async def save_thumbnail(
        self,
        file: BinaryIO,
        document_id: int,
        page_number: int
    ) -> str:
        """
        Speichere Thumbnail.
        
        Args:
            file: File-like Object (Binary)
            document_id: Dokument ID
            page_number: Seitennummer
            
        Returns:
            Relativer Pfad zum gespeicherten Thumbnail
        """
        date_path = self._get_date_path()
        target_dir = self.thumbnails_path / date_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"doc_{document_id}_page_{page_number}_thumb.jpg"
        target_path = target_dir / filename
        
        try:
            with open(target_path, 'wb') as f:
                shutil.copyfileobj(file, f)
        except Exception as e:
            raise IOError(f"Failed to save thumbnail: {e}")
        
        return str(target_path.relative_to(self.base_path))
    
    async def get_document(self, relative_path: str) -> BinaryIO:
        """
        Lade Original-Dokument.
        
        Args:
            relative_path: Relativer Pfad
            
        Returns:
            File-like Object (Binary)
            
        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
        """
        full_path = self.base_path / relative_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Document not found: {relative_path}")
        
        return open(full_path, 'rb')
    
    async def get_preview(self, relative_path: str) -> BinaryIO:
        """
        Lade Preview-Bild.
        
        Args:
            relative_path: Relativer Pfad
            
        Returns:
            File-like Object (Binary)
        """
        full_path = self.base_path / relative_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Preview not found: {relative_path}")
        
        return open(full_path, 'rb')
    
    async def delete_document(self, relative_path: str) -> bool:
        """
        Lösche Dokument.
        
        Args:
            relative_path: Relativer Pfad
            
        Returns:
            True wenn erfolgreich
        """
        full_path = self.base_path / relative_path
        
        if not full_path.exists():
            return False
        
        try:
            full_path.unlink()
            return True
        except Exception:
            return False
    
    async def delete_previews(self, document_id: int) -> int:
        """
        Lösche alle Previews eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Dateien
        """
        count = 0
        pattern = f"doc_{document_id}_page_*.jpg"
        
        # Durchsuche alle Datums-Verzeichnisse
        for preview_file in self.previews_path.rglob(pattern):
            try:
                preview_file.unlink()
                count += 1
            except Exception:
                pass
        
        return count
    
    async def delete_thumbnails(self, document_id: int) -> int:
        """
        Lösche alle Thumbnails eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Dateien
        """
        count = 0
        pattern = f"doc_{document_id}_page_*_thumb.jpg"
        
        for thumb_file in self.thumbnails_path.rglob(pattern):
            try:
                thumb_file.unlink()
                count += 1
            except Exception:
                pass
        
        return count
    
    def get_absolute_path(self, relative_path: str) -> str:
        """
        Konvertiere relativen Pfad zu absolutem Pfad.
        
        Args:
            relative_path: Relativer Pfad
            
        Returns:
            Absoluter Pfad
        """
        return str((self.base_path / relative_path).absolute())

