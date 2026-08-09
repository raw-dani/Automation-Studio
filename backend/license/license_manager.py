"""
License Manager - Kelola aktivasi, verifikasi, dan deaktivasi lisensi WHMCS.
"""

import json
import os
import time
import requests
from typing import Optional, Dict, Any

from backend.license.fingerprint import get_fingerprint


class LicenseManager:
    """Manager untuk lisensi aplikasi."""

    def __init__(self, config: dict):
        self.config = config
        self.server_url = config.get("server_url", "")
        self.api_key = config.get("api_key", "")
        self.verify_interval_hours = config.get("verify_interval_hours", 24)
        self.auto_verify_on_start = config.get("auto_verify_on_start", True)

        self._license_data: Optional[dict] = None
        self._last_verify_time: float = 0
        self._license_file = os.path.join("data", "license.json")

        # Load license lokal jika ada
        self._load_local_license()

    def _load_local_license(self):
        """Load data lisensi dari file lokal."""
        if not os.path.exists(self._license_file):
            self._license_data = None
            return

        try:
            with open(self._license_file, "r", encoding="utf-8") as f:
                self._license_data = json.load(f)
        except Exception:
            self._license_data = None

    def _save_local_license(self, data: dict):
        """Simpan data lisensi ke file lokal."""
        os.makedirs(os.path.dirname(self._license_file), exist_ok=True)
        with open(self._license_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._license_data = data

    def _clear_local_license(self):
        """Hapus data lisensi lokal."""
        self._license_data = None
        if os.path.exists(self._license_file):
            try:
                os.remove(self._license_file)
            except Exception:
                pass

    def get_fingerprint(self) -> str:
        """Dapatkan fingerprint hardware saat ini."""
        return get_fingerprint()

    def is_licensed(self) -> bool:
        """
        Cek apakah aplikasi berlisensi.
        Returns True jika:
        - Ada license data lokal
        - Status adalah 'licensed'
        - Verifikasi terakhir masih dalam TTL (24 jam)
        - Atau offline mode dengan cache valid
        """
        if not self._license_data:
            return False

        if self._license_data.get("status") != "licensed":
            return False

        # Cek apakah verifikasi sudah kadaluarsa
        last_verify = self._license_data.get("last_verify_at", 0)
        if isinstance(last_verify, str):
            try:
                last_verify = time.mktime(time.strptime(last_verify, "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                last_verify = 0

        ttl_seconds = self.verify_interval_hours * 3600
        if time.time() - last_verify > ttl_seconds:
            # Cache expired, coba verifikasi ulang
            if self.verify():
                return True
            # Jika verifikasi gagal, anggap tidak berlisensi
            return False

        return True

    def activate(self, license_key: str) -> Dict[str, Any]:
        """
        Aktivasi lisensi dengan license key.
        Bind lisensi ke hardware fingerprint saat ini.
        """
        if not license_key or not license_key.strip():
            return {"success": False, "message": "License key tidak boleh kosong"}

        if not self.server_url:
            return {"success": False, "message": "Server URL belum dikonfigurasi"}

        license_key = license_key.strip()
        fingerprint = self.get_fingerprint()

        try:
            payload = {
                "action": "activate",
                "license_key": license_key,
                "fingerprint": fingerprint,
                "domain": "localhost",
            }

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.post(
                self.server_url,
                data=payload,
                headers=headers,
                timeout=30,
            )

            result = response.json()

            if result.get("status") == "success" and result.get("code") == 200:
                # Simpan data lisensi lokal
                license_data = {
                    "license_key": license_key,
                    "fingerprint": fingerprint,
                    "activated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "last_verify_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "status": "licensed",
                    "token": result.get("data", {}).get("token", ""),
                    "expires_in": result.get("data", {}).get("expires_in", 86400),
                }
                self._save_local_license(license_data)
                return {
                    "success": True,
                    "message": result.get("message", "License activated successfully"),
                    "data": result.get("data", {}),
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Activation failed"),
                    "code": result.get("code"),
                }

        except requests.exceptions.Timeout:
            return {"success": False, "message": "Koneksi ke server timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Tidak dapat terhubung ke server. Periksa koneksi internet."}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def verify(self) -> bool:
        """
        Verifikasi lisensi dengan server.
        Returns True jika lisensi valid, False jika tidak.
        """
        if not self._license_data:
            return False

        if not self.server_url:
            # Tidak ada server, anggap valid jika ada cache (offline mode)
            return True

        license_key = self._license_data.get("license_key", "")
        fingerprint = self._license_data.get("fingerprint", "")

        if not license_key or not fingerprint:
            return False

        try:
            payload = {
                "action": "verify",
                "license_key": license_key,
                "fingerprint": fingerprint,
                "domain": "localhost",
            }

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.post(
                self.server_url,
                data=payload,
                headers=headers,
                timeout=30,
            )

            result = response.json()

            if result.get("status") == "success" and result.get("code") == 200:
                # Update last_verify_at
                self._license_data["last_verify_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                self._license_data["token"] = result.get("data", {}).get("token", "")
                self._save_local_license(self._license_data)
                self._last_verify_time = time.time()
                return True
            else:
                # Verifikasi gagal
                if result.get("code") == 403 and "fingerprint" in result.get("message", "").lower():
                    # Fingerprint mismatch
                    self._license_data["status"] = "mismatch"
                    self._save_local_license(self._license_data)
                return False

        except Exception:
            # Jika error koneksi, tetap anggap valid (offline mode)
            return True

    def deactivate(self) -> Dict[str, Any]:
        """
        Nonaktifkan lisensi dari komputer ini.
        """
        if not self._license_data:
            return {"success": False, "message": "Tidak ada lisensi yang aktif"}

        if not self.server_url:
            # Offline mode, hapus saja data lokal
            self._clear_local_license()
            return {"success": True, "message": "License deactivated (offline mode)"}

        license_key = self._license_data.get("license_key", "")
        fingerprint = self._license_data.get("fingerprint", "")

        try:
            payload = {
                "action": "deactivate",
                "license_key": license_key,
                "fingerprint": fingerprint,
            }

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.post(
                self.server_url,
                data=payload,
                headers=headers,
                timeout=30,
            )

            result = response.json()

            # Hapus data lokal
            self._clear_local_license()

            if result.get("status") == "success":
                return {"success": True, "message": result.get("message", "License deactivated")}
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Deactivation failed"),
                    "code": result.get("code"),
                }

        except Exception as e:
            # Tetap hapus data lokal meskipun server error
            self._clear_local_license()
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        """
        Dapatkan status lisensi saat ini.
        """
        if not self._license_data:
            return {
                "status": "unlicensed",
                "message": "Tidak ada lisensi yang aktif. Mode Free: 10 data/hari.",
                "licensed": False,
                "fingerprint": self.get_fingerprint(),
            }

        license_status = self._license_data.get("status", "unknown")
        last_verify = self._license_data.get("last_verify_at", "")

        if license_status == "licensed":
            # Cek apakah verifikasi sudah kadaluarsa
            if isinstance(last_verify, str) and last_verify:
                try:
                    last_verify_ts = time.mktime(time.strptime(last_verify, "%Y-%m-%dT%H:%M:%S"))
                    ttl_seconds = self.verify_interval_hours * 3600
                    if time.time() - last_verify_ts > ttl_seconds:
                        # Cache expired
                        return {
                            "status": "expired",
                            "message": "Verifikasi lisensi kadaluarsa. Silakan verifikasi ulang.",
                            "licensed": False,
                            "fingerprint": self._license_data.get("fingerprint", ""),
                        }
                except Exception:
                    pass

            return {
                "status": "licensed",
                "message": "Lisensi aktif. Mode Licensed: tanpa batasan.",
                "licensed": True,
                "fingerprint": self._license_data.get("fingerprint", ""),
                "activated_at": self._license_data.get("activated_at", ""),
                "last_verify": last_verify,
            }

        elif license_status == "mismatch":
            return {
                "status": "mismatch",
                "message": "Lisensi terdaftar untuk hardware berbeda. Silakan deaktivasi dan aktivasi ulang.",
                "licensed": False,
                "fingerprint": self._license_data.get("fingerprint", ""),
            }

        else:
            return {
                "status": license_status,
                "message": f"Status lisensi: {license_status}",
                "licensed": False,
                "fingerprint": self._license_data.get("fingerprint", ""),
            }

    def get_remaining_quota(self, usage_tracker) -> int:
        """
        Dapatkan sisa kuota data hari ini (untuk free mode).
        """
        if self.is_licensed():
            return -1  # Unlimited

        return usage_tracker.get_remaining_quota()

    def auto_verify_on_startup(self):
        """
        Auto-verifikasi lisensi saat aplikasi start.
        Returns True jika valid atau offline mode dengan cache valid.
        """
        if not self.auto_verify_on_start:
            return True

        if not self._license_data:
            # Belum ada lisensi, free mode
            return True

        # Cek apakah verifikasi sudah kadaluarsa
        last_verify = self._license_data.get("last_verify_at", 0)
        if isinstance(last_verify, str):
            try:
                last_verify = time.mktime(time.strptime(last_verify, "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                last_verify = 0

        ttl_seconds = self.verify_interval_hours * 3600
        if time.time() - last_verify > ttl_seconds:
            # Cache expired, coba verifikasi
            return self.verify()

        return True