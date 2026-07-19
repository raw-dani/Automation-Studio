"""
Image Detection - Mendeteksi elemen visual pada gambar menggunakan OpenCV.
Berguna untuk automasi yang tidak bisa menggunakan selector biasa.
"""

import os
from typing import Optional
from loguru import logger

from backend.detectors.base_detector import BaseDetector, DetectionResult


class ImageDetector(BaseDetector):
    """
    Mendeteksi template/gambar di dalam screenshot menggunakan template matching.
    Berguna untuk aplikasi desktop atau web yang tidak memiliki selector unik.
    """
    
    @property
    def name(self) -> str:
        return "image_detection"
    
    def detect(
        self,
        image_path: str,
        template_path: str = "",
        threshold: float = 0.8,
        method: str = "cv2.TM_CCOEFF_NORMED",
        **kwargs,
    ) -> DetectionResult:
        """
        Cari template di dalam gambar.
        
        Args:
            image_path: Path ke screenshot/gambar utama.
            template_path: Path ke template yang akan dicari.
            threshold: Threshold confidence (0.0 - 1.0).
            method: Template matching method.
            
        Returns:
            DetectionResult dengan posisi template jika ditemukan.
        """
        if not os.path.exists(image_path):
            return DetectionResult(
                success=False,
                message=f"File gambar tidak ditemukan: {image_path}",
            )
        
        if not os.path.exists(template_path):
            return DetectionResult(
                success=False,
                message=f"File template tidak ditemukan: {template_path}",
            )
        
        try:
            import cv2
            import numpy as np
            
            # Baca gambar
            img = cv2.imread(image_path)
            template = cv2.imread(template_path)
            
            if img is None:
                return DetectionResult(
                    success=False,
                    message=f"Gagal membaca gambar: {image_path}",
                )
            
            if template is None:
                return DetectionResult(
                    success=False,
                    message=f"Gagal membaca template: {template_path}",
                )
            
            # Convert to grayscale
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # Dapatkan lokasi dengan confidence tertinggi
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            h, w = template_gray.shape
            
            # Cari semua matches di atas threshold
            locations = np.where(result >= threshold)
            matches = []
            
            for pt in zip(*locations[::-1]):
                matches.append({
                    "x": int(pt[0]),
                    "y": int(pt[1]),
                    "width": w,
                    "height": h,
                    "confidence": float(result[pt[1], pt[0]]),
                    "center_x": int(pt[0] + w / 2),
                    "center_y": int(pt[1] + h / 2),
                })
            
            # Non-maximum suppression untuk menghilangkan overlap
            if len(matches) > 1:
                matches = self._non_max_suppression(matches, 0.5)
            
            if matches:
                best_match = max(matches, key=lambda m: m["confidence"])
                
                return DetectionResult(
                    success=True,
                    data={
                        "found": True,
                        "matches": matches,
                        "match_count": len(matches),
                        "best_match": best_match,
                        "template_size": {"width": w, "height": h},
                        "image_size": {
                            "width": img.shape[1],
                            "height": img.shape[0],
                        },
                    },
                    confidence=best_match["confidence"],
                    message=f"Template ditemukan di ({best_match['center_x']}, {best_match['center_y']}) dengan confidence {best_match['confidence']:.2%}",
                )
            else:
                return DetectionResult(
                    success=True,
                    data={
                        "found": False,
                        "matches": [],
                        "match_count": 0,
                        "best_match": None,
                        "max_confidence": float(max_val),
                    },
                    confidence=float(max_val),
                    message=f"Template tidak ditemukan (max confidence: {max_val:.2%})",
                )
                
        except ImportError as e:
            return DetectionResult(
                success=False,
                message="OpenCV (cv2) tidak terinstall",
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Image detection failed: {e}")
            return DetectionResult(
                success=False,
                message=f"Image detection gagal: {str(e)}",
                error=str(e),
            )
    
    def detect_by_color(
        self,
        image_path: str,
        target_color: tuple,
        tolerance: int = 30,
    ) -> DetectionResult:
        """
        Deteksi region berdasarkan warna.
        
        Args:
            image_path: Path ke file gambar.
            target_color: Warna target dalam BGR format (b, g, r).
            tolerance: Tolerance warna (0-255).
            
        Returns:
            DetectionResult dengan region yang cocok.
        """
        if not os.path.exists(image_path):
            return DetectionResult(
                success=False,
                message=f"File tidak ditemukan: {image_path}",
            )
        
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(image_path)
            if img is None:
                return DetectionResult(
                    success=False,
                    message="Gagal membaca gambar",
                )
            
            # Buat mask untuk warna target
            lower = np.array([max(0, c - tolerance) for c in target_color])
            upper = np.array([min(255, c + tolerance) for c in target_color])
            mask = cv2.inRange(img, lower, upper)
            
            # Cari contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if area > 100:  # Filter noise
                    regions.append({
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "area": area,
                        "center_x": x + w // 2,
                        "center_y": y + h // 2,
                    })
            
            return DetectionResult(
                success=True,
                data={
                    "regions": regions,
                    "region_count": len(regions),
                    "target_color": target_color,
                    "tolerance": tolerance,
                },
                message=f"{len(regions)} region dengan warna terdeteksi",
            )
            
        except ImportError:
            return DetectionResult(
                success=False,
                message="OpenCV (cv2) tidak terinstall",
            )
        except Exception as e:
            return DetectionResult(
                success=False,
                message=f"Color detection gagal: {str(e)}",
                error=str(e),
            )
    
    def _non_max_suppression(self, matches: list, overlap_threshold: float = 0.5) -> list:
        """
        Non-maximum suppression untuk menghilangkan bounding boxes yang overlap.
        """
        if not matches:
            return []
        
        # Sort by confidence descending
        matches = sorted(matches, key=lambda m: m["confidence"], reverse=True)
        
        selected = []
        while matches:
            best = matches.pop(0)
            selected.append(best)
            
            # Hapus matches yang overlap dengan best
            matches = [
                m for m in matches
                if not self._is_overlap(best, m, overlap_threshold)
            ]
        
        return selected
    
    def _is_overlap(self, box1: dict, box2: dict, threshold: float) -> bool:
        """Cek apakah dua bounding boxes overlap."""
        x1 = max(box1["x"], box2["x"])
        y1 = max(box1["y"], box2["y"])
        x2 = min(box1["x"] + box1["width"], box2["x"] + box2["width"])
        y2 = min(box1["y"] + box1["height"], box2["y"] + box2["height"])
        
        if x2 <= x1 or y2 <= y1:
            return False
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = box1["width"] * box1["height"]
        
        return intersection / area1 > threshold