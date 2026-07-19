"""
OCR Detector - Membaca teks dari gambar menggunakan Tesseract OCR.
"""

import os
from typing import Optional
from loguru import logger

from backend.detectors.base_detector import BaseDetector, DetectionResult


class OCRDetector(BaseDetector):
    """
    Mendeteksi dan membaca teks dari gambar menggunakan Tesseract OCR.
    
    Requirements:
        - Tesseract harus terinstall di sistem
        - Atur path tesseract di config.yaml atau environment variable TESSERACT_PATH
    """
    
    @property
    def name(self) -> str:
        return "ocr"
    
    def _get_tesseract_path(self) -> Optional[str]:
        """Dapatkan path tesseract dari environment variable."""
        return os.environ.get("TESSERACT_PATH")
    
    def detect(
        self,
        image_path: str,
        lang: str = "eng+ind",
        psm: int = 3,
        **kwargs,
    ) -> DetectionResult:
        """
        Baca teks dari gambar.
        
        Args:
            image_path: Path ke file gambar.
            lang: Bahasa (default: eng+ind untuk English + Indonesian).
            psm: Page segmentation mode (default: 3 = automatic).
            
        Returns:
            DetectionResult dengan teks yang terdeteksi.
        """
        if not os.path.exists(image_path):
            return DetectionResult(
                success=False,
                message=f"File tidak ditemukan: {image_path}",
                error="File not found",
            )
        
        try:
            import pytesseract
            from PIL import Image
            
            # Set tesseract path jika ada
            tesseract_path = self._get_tesseract_path()
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Buka gambar
            image = Image.open(image_path)
            
            # OCR
            custom_config = f"--psm {psm}"
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=custom_config,
            )
            
            # Dapatkan confidence data
            try:
                data = pytesseract.image_to_data(
                    image,
                    lang=lang,
                    config=custom_config,
                    output_type=pytesseract.Output.DICT,
                )
                
                # Hitung confidence rata-rata
                confidences = [c for c in data["conf"] if c != -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except Exception:
                avg_confidence = 0.0
            
            cleaned_text = text.strip()
            
            if cleaned_text:
                return DetectionResult(
                    success=True,
                    data={
                        "text": cleaned_text,
                        "length": len(cleaned_text),
                        "lines": cleaned_text.split("\n"),
                    },
                    confidence=avg_confidence,
                    message=f"OCR berhasil: {len(cleaned_text)} karakter terdeteksi",
                )
            else:
                return DetectionResult(
                    success=True,
                    data={"text": "", "length": 0, "lines": []},
                    confidence=0,
                    message="Tidak ada teks terdeteksi",
                )
                
        except ImportError as e:
            return DetectionResult(
                success=False,
                message="pytesseract atau Pillow tidak terinstall",
                error=str(e),
            )
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return DetectionResult(
                success=False,
                message=f"OCR gagal: {str(e)}",
                error=str(e),
            )
    
    def detect_text_regions(
        self,
        image_path: str,
        lang: str = "eng+ind",
    ) -> DetectionResult:
        """
        Deteksi region teks dengan bounding boxes.
        
        Returns:
            DetectionResult dengan list region: [{text, x, y, w, h, confidence}, ...]
        """
        if not os.path.exists(image_path):
            return DetectionResult(
                success=False,
                message=f"File tidak ditemukan: {image_path}",
            )
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                output_type=pytesseract.Output.DICT,
            )
            
            regions = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    regions.append({
                        "text": data["text"][i],
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "w": data["width"][i],
                        "h": data["height"][i],
                        "confidence": data["conf"][i],
                    })
            
            return DetectionResult(
                success=True,
                data={"regions": regions, "count": len(regions)},
                message=f"{len(regions)} text regions terdeteksi",
            )
            
        except Exception as e:
            return DetectionResult(
                success=False,
                message=f"Text region detection gagal: {str(e)}",
                error=str(e),
            )