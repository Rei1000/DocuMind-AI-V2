"""
Image Processor Service für Document Upload Context

Verantwortlich für Bildverarbeitung:
- Thumbnail-Generierung
- Auto-Rotation
- Quality Check
- Format-Konvertierung
"""

import io
from typing import Optional, BinaryIO
from PIL import Image, ImageOps
from pathlib import Path


class ImageProcessorService:
    """
    Image Processor Service.
    
    Features:
    - Thumbnail-Generierung mit Aspect Ratio
    - Auto-Rotation (EXIF-basiert)
    - Quality Check (Lesbarkeit)
    - Format-Konvertierung (PNG → JPG, etc.)
    
    Args:
        thumbnail_size: Thumbnail-Größe (default: (200, 200))
        jpeg_quality: JPEG-Qualität (default: 85)
    """
    
    def __init__(
        self,
        thumbnail_size: tuple[int, int] = (200, 200),
        jpeg_quality: int = 85
    ):
        self.thumbnail_size = thumbnail_size
        self.jpeg_quality = jpeg_quality
    
    async def create_thumbnail(
        self,
        image: Image.Image,
        maintain_aspect_ratio: bool = True
    ) -> Image.Image:
        """
        Erstelle Thumbnail.
        
        Args:
            image: PIL Image
            maintain_aspect_ratio: Seitenverhältnis beibehalten
            
        Returns:
            Thumbnail als PIL Image
        """
        thumbnail = image.copy()
        
        if maintain_aspect_ratio:
            # Thumbnail mit Aspect Ratio
            thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
        else:
            # Thumbnail ohne Aspect Ratio (Crop)
            thumbnail = ImageOps.fit(
                thumbnail,
                self.thumbnail_size,
                Image.Resampling.LANCZOS
            )
        
        return thumbnail
    
    async def auto_rotate(self, image: Image.Image) -> Image.Image:
        """
        Auto-Rotation basierend auf EXIF-Daten.
        
        Args:
            image: PIL Image
            
        Returns:
            Rotiertes Image
        """
        try:
            # EXIF-Orientierung anwenden
            image = ImageOps.exif_transpose(image)
        except Exception:
            # Kein EXIF oder Fehler → Original returnieren
            pass
        
        return image
    
    async def convert_to_jpeg(
        self,
        image: Image.Image,
        quality: Optional[int] = None
    ) -> bytes:
        """
        Konvertiere Image zu JPEG-Bytes.
        
        Args:
            image: PIL Image
            quality: JPEG-Qualität (optional, default: self.jpeg_quality)
            
        Returns:
            JPEG als Bytes
        """
        if quality is None:
            quality = self.jpeg_quality
        
        # Konvertiere zu RGB (JPEG unterstützt kein Alpha-Channel)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Erstelle weißen Hintergrund
            background = Image.new('RGB', image.size, (255, 255, 255))
            
            if image.mode == 'P':
                image = image.convert('RGBA')
            
            # Composite mit weißem Hintergrund
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1])  # Alpha-Channel als Mask
                image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Schreibe zu Bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output.getvalue()
    
    async def convert_to_png(self, image: Image.Image) -> bytes:
        """
        Konvertiere Image zu PNG-Bytes.
        
        Args:
            image: PIL Image
            
        Returns:
            PNG als Bytes
        """
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        return output.getvalue()
    
    async def check_quality(
        self,
        image: Image.Image,
        min_width: int = 500,
        min_height: int = 500
    ) -> dict:
        """
        Prüfe Bild-Qualität.
        
        Args:
            image: PIL Image
            min_width: Minimale Breite
            min_height: Minimale Höhe
            
        Returns:
            Dict mit Quality-Metriken:
            {
                'is_readable': bool,
                'width': int,
                'height': int,
                'aspect_ratio': float,
                'warnings': List[str]
            }
        """
        warnings = []
        
        width, height = image.size
        aspect_ratio = width / height
        
        # Prüfe Mindest-Dimensionen
        if width < min_width:
            warnings.append(f"Width {width}px below minimum {min_width}px")
        
        if height < min_height:
            warnings.append(f"Height {height}px below minimum {min_height}px")
        
        # Prüfe extremes Seitenverhältnis
        if aspect_ratio < 0.3 or aspect_ratio > 3.0:
            warnings.append(f"Unusual aspect ratio: {aspect_ratio:.2f}")
        
        is_readable = len(warnings) == 0
        
        return {
            'is_readable': is_readable,
            'width': width,
            'height': height,
            'aspect_ratio': aspect_ratio,
            'warnings': warnings
        }
    
    async def resize_image(
        self,
        image: Image.Image,
        max_width: int,
        max_height: int,
        maintain_aspect_ratio: bool = True
    ) -> Image.Image:
        """
        Resize Image.
        
        Args:
            image: PIL Image
            max_width: Maximale Breite
            max_height: Maximale Höhe
            maintain_aspect_ratio: Seitenverhältnis beibehalten
            
        Returns:
            Resized Image
        """
        if maintain_aspect_ratio:
            # Berechne neue Dimensionen unter Beibehaltung des Aspect Ratio
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            return image
        else:
            # Resize ohne Aspect Ratio
            return image.resize((max_width, max_height), Image.Resampling.LANCZOS)
    
    async def load_image_from_bytes(self, image_bytes: bytes) -> Image.Image:
        """
        Lade Image aus Bytes.
        
        Args:
            image_bytes: Image als Bytes
            
        Returns:
            PIL Image
            
        Raises:
            ValueError: Wenn Image ungültig
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return image
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")
    
    async def load_image_from_path(self, image_path: str) -> Image.Image:
        """
        Lade Image aus Datei.
        
        Args:
            image_path: Pfad zum Image
            
        Returns:
            PIL Image
            
        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            ValueError: Wenn Image ungültig
        """
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            image = Image.open(path)
            return image
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")

