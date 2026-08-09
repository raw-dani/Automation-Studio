"""
Hardware Fingerprint - Generate unique fingerprint untuk 1 komputer.
Menggunakan kombinasi: MachineGuid/MachineId + MAC Address + Disk Serial + Hostname.
"""

import hashlib
import platform
import subprocess
import os
import sys
from typing import Optional


def _get_machine_guid() -> str:
    """
    Ambil machine GUID.
    - Windows: dari registry HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography
    - Linux: dari /etc/machine-id
    - macOS: dari IOPlatformUUID
    """
    system = platform.system()
    try:
        if system == "Windows":
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\\Microsoft\\Cryptography",
                    access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "MachineGuid")
                    if value:
                        return str(value).strip()
            except Exception:
                pass
            # Fallback: product ID
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                    access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "ProductID")
                    if value:
                        return str(value).strip()
            except Exception:
                pass

        elif system == "Linux":
            paths = ["/etc/machine-id", "/var/lib/dbus/machine-id"]
            for path in paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        value = f.read().strip()
                    if value:
                        return value

        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True, text=True, check=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "IOPlatformUUID" in line:
                        # Format: "IOPlatformUUID" = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                        value = line.split('"')[3]
                        if value:
                            return value
            except Exception:
                pass
    except Exception:
        pass
    return ""


def _get_mac_address() -> str:
    """Ambil MAC address dari network interface aktif."""
    try:
        if platform.system() == "Windows":
            # Gunakan netsh
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=5
            )
            # Cari interface yang Connected
            for line in result.stdout.splitlines():
                if "Connected" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        iface_name = parts[-1]
                        # Dapatkan MAC address
                        result2 = subprocess.run(
                            ["getmac", "/v", "/fo", "csv", "/nh"],
                            capture_output=True, text=True, timeout=5
                        )
                        for row in result2.stdout.splitlines():
                            if iface_name in row:
                                mac = row.split(",")[1].strip().strip('"')
                                if mac and mac != "N/A":
                                    return mac.replace("-", ":").upper()
        else:
            # Linux/macOS
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "link/ether" in line:
                    mac = line.split()[1]
                    return mac.upper()
    except Exception:
        pass
    return ""


def _get_disk_serial() -> str:
    """Ambil serial disk utama."""
    system = platform.system()
    try:
        if system == "Windows":
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                    access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "InstallTime")
                    if value:
                        return str(value)
            except Exception:
                pass
            # Fallback: volume serial
            try:
                result = subprocess.run(
                    ["cmd", "/c", "vol", "C:"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "Serial Number" in line:
                        serial = line.split("Serial Number")[-1].strip()
                        if serial:
                            return serial
            except Exception:
                pass

        elif system == "Linux":
            paths = ["/etc/machine-id", "/var/lib/dbus/machine-id"]
            for path in paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        return f.read().strip()

        elif system == "Darwin":  # macOS
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, check=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    value = line.split('"')[3]
                    if value:
                        return value
    except Exception:
        pass
    return ""


def _get_hostname() -> str:
    """Ambil hostname komputer."""
    try:
        return platform.node() or ""
    except Exception:
        return ""


def get_fingerprint() -> str:
    """
    Generate hardware fingerprint yang unik untuk komputer ini.
    Kombinasi: machine_guid + mac + disk_serial + hostname
    Return: SHA-256 hash string (hex digest)
    """
    components = [
        _get_machine_guid(),
        _get_mac_address(),
        _get_disk_serial(),
        _get_hostname(),
    ]

    # Gabungkan dengan delimiter yang tidak mungkin muncul di identifier
    raw = "|".join(components)
    if not raw or raw == "||||":
        # Fallback jika semua gagal: gunakan hostname + platform
        raw = f"{_get_hostname()}|{platform.system()}|{platform.machine()}"

    # Hash dengan SHA-256
    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return fingerprint


if __name__ == "__main__":
    # Test: print fingerprint dan pastikan konsisten
    fp1 = get_fingerprint()
    fp2 = get_fingerprint()
    print(f"Fingerprint: {fp1}")
    print(f"Consistent: {fp1 == fp2}")