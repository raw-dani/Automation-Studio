"""
Usage Tracker - Lacak penggunaan data harian untuk free mode.
Membatasi 10 data per hari jika tidak ada lisensi.
"""

import json
import os
from datetime import datetime, date
from typing import Optional


class UsageTracker:
    """Tracker untuk penggunaan data harian."""

    def __init__(self, daily_limit: int = 10):
        self.daily_limit = daily_limit
        self._usage_file = os.path.join("data", "usage.json")
        self._today_usage = 0
        self._today_date = ""
        self._load_or_reset()

    def _load_or_reset(self):
        """Load data usage atau reset jika hari berganti."""
        today = str(date.today())

        if os.path.exists(self._usage_file):
            try:
                with open(self._usage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                saved_date = data.get("date", "")
                if saved_date == today:
                    self._today_date = today
                    self._today_usage = data.get("processed_count", 0)
                    return
            except Exception:
                pass

        # Reset untuk hari baru
        self._today_date = today
        self._today_usage = 0
        self._save()

    def _save(self):
        """Simpan data usage ke file."""
        os.makedirs(os.path.dirname(self._usage_file), exist_ok=True)
        data = {
            "date": self._today_date,
            "processed_count": self._today_usage,
            "daily_limit": self.daily_limit,
        }
        with open(self._usage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_today_usage(self) -> int:
        """Dapatkan jumlah data yang diproses hari ini."""
        self._load_or_reset()
        return self._today_usage

    def increment_usage(self, count: int = 1):
        """Tambah jumlah data yang diproses."""
        self._load_or_reset()
        self._today_usage += count
        self._save()

    def get_remaining_quota(self) -> int:
        """Dapatkan sisa kuota (negative = unlimited)."""
        self._load_or_reset()
        remaining = self.daily_limit - self._today_usage
        return max(0, remaining)

    def is_quota_exceeded(self) -> bool:
        """Cek apakah kuota sudah habis."""
        self._load_or_reset()
        return self._today_usage >= self.daily_limit

    def reset_daily(self):
        """Reset counter untuk hari ini."""
        self._today_date = str(date.today())
        self._today_usage = 0
        self._save()