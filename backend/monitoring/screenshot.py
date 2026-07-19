"""
Screenshot Manager - Mengelola screenshot otomatis saat eksekusi workflow.
"""

import os
from datetime import datetime
from typing import Optional
from loguru import logger


class ScreenshotManager:
    """
    Manager untuk mengambil dan menyimpan screenshot.
    
    Contoh:
        sm = ScreenshotManager("screenshots")
        path = await sm.capture(page, "step_1", is_error=True)
    """
    
    def __init__(self, screenshots_dir: str = "screenshots"):
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)
    
    def _generate_filename(self, step_id: str, is_error: bool = False) -> str:
        """Generate unique filename untuk screenshot."""
        prefix = "error" if is_error else "step"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"{prefix}_{step_id}_{timestamp}.png"
    
    async def capture(
        self,
        page,
        step_id: str,
        is_error: bool = False,
        full_page: bool = False,
    ) -> Optional[str]:
        """
        Ambil screenshot dari halaman.
        
        Args:
            page: Playwright page object.
            step_id: ID step yang sedang dieksekusi.
            is_error: Apakah screenshot karena error.
            full_page: Screenshot full page atau viewport saja.
            
        Returns:
            Path file screenshot, atau None jika gagal.
        """
        if not page:
            logger.warning("No page available for screenshot")
            return None
        
        filename = self._generate_filename(step_id, is_error)
        filepath = os.path.join(self.screenshots_dir, filename)
        
        try:
            await page.screenshot(path=filepath, full_page=full_page)
            logger.info(f"Screenshot saved: {filename}")
            return filepath
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")
            return None
    
    def get_screenshot_path(self, filename: str) -> str:
        """Dapatkan full path dari screenshot file."""
        return os.path.join(self.screenshots_dir, filename)
    
    def list_screenshots(self, execution_id: Optional[str] = None) -> list[dict]:
        """
        List semua screenshot yang tersedia.
        
        Args:
            execution_id: Filter by execution ID (prefix filename).
            
        Returns:
            List of dict: [{"filename": "...", "path": "...", "size": ..., "created": "..."}, ...]
        """
        if not os.path.exists(self.screenshots_dir):
            return []
        
        screenshots = []
        for f in os.listdir(self.screenshots_dir):
            if not f.endswith((".png", ".jpg", ".jpeg")):
                continue
            
            if execution_id and not f.startswith(execution_id):
                continue
            
            filepath = os.path.join(self.screenshots_dir, f)
            stat = os.stat(filepath)
            
            screenshots.append({
                "filename": f,
                "path": filepath,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
        
        return sorted(screenshots, key=lambda x: x["created"], reverse=True)
    
    def cleanup(self, max_age_days: int = 30) -> int:
        """
        Hapus screenshot lama.
        
        Args:
            max_age_days: Hapus screenshot lebih dari N hari.
            
        Returns:
            Jumlah file yang dihapus.
        """
        if not os.path.exists(self.screenshots_dir):
            return 0
        
        now = datetime.now().timestamp()
        max_age = max_age_days * 86400  # Convert to seconds
        deleted = 0
        
        for f in os.listdir(self.screenshots_dir):
            if not f.endswith((".png", ".jpg", ".jpeg")):
                continue
            
            filepath = os.path.join(self.screenshots_dir, f)
            file_age = now - os.stat(filepath).st_mtime
            
            if file_age > max_age:
                os.remove(filepath)
                deleted += 1
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old screenshots")
        
        return deleted