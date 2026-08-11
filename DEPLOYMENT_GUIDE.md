# Panduan Distribusi Automation Studio ke Customer

Dokumen ini menjelaskan langkah-langkah membuat, packaging, dan mendistribusikan aplikasi Automation Studio ke customer dalam bentuk file `.exe` yang tinggal diklik.

---

## 1. Prasyarat

- Python 3.10+ sudah terinstal
- Semua dependency terinstal:
  ```bash
  pip install -r requirements.txt
  ```
- PyInstaller 6.0+ terinstal:
  ```bash
  pip install pyinstaller
  ```
- Playwright browser terinstal:
  ```bash
  playwright install chromium
  ```

---

## 2. Build Executable (.exe)

Jalankan perintah berikut di folder proyek:

```bash
python build_exe.py
```

Setelah build selesai, folder hasil build akan ada di:
```
dist/AutomationStudio/AutomationStudio.exe
```

### Build Versi Lain (Opsional)
```bash
python build_exe.py --cli    # Build versi CLI
python build_exe.py --api    # Build versi API server
```

---

## 3. Struktur Folder Hasil Build

Setelah build, struktur folder yang akan didistribusikan:

```
dist/
└── AutomationStudio/
    ├── AutomationStudio.exe      # File utama
    ├── _internal/                 # Semua library dan module
    ├── config.yaml               # Konfigurasi aplikasi
    ├── workflows/                # Folder workflow (bisa kosong)
    ├── data/                     # Folder data (bisa kosong)
    ├── logs/                     # Folder log (akan dibuat otomatis)
    └── screenshots/              # Folder screenshot (akan dibuat otomatis)
```

---

## 4. Packaging untuk Distribusi

Buat file ZIP dari folder `dist/AutomationStudio/`:

```
AutomationStudio_v1.0.0.zip
```

Atau gunakan tools seperti WinRAR/7-Zip untuk membuat installer yang lebih ramah pengguna.

### Checklist Sebelum Distribusi
- [x] Build `.exe` berhasil tanpa error
- [x] File `config.yaml` sudah disertakan
- [x] Folder `workflows`, `data`, `logs`, `screenshots` sudah disertakan
- [x] Ukuran file ZIP sudah sesuai (cek tidak ada file sampah)
- [x] Test run di komputer lain (jika memungkinkan)

---

## 5. Cara Menjalankan di Komputer Customer

1. Ekstrak file ZIP `AutomationStudio_v1.0.0.zip`
2. Buka folder `AutomationStudio`
3. Double-click file `AutomationStudio.exe`
4. Aplikasi akan berjalan tanpa jendela console (GUI mode)

### Catatan Penting
- **Tidak perlu install Python** di komputer customer, karena sudah dibundle dalam `.exe`
- **Tidak perlu install dependency** apapun, semua sudah included
- **Data dan workflow** akan disimpan di folder yang sama dengan aplikasi
- **Lisensi** akan terbind ke hardware komputer customer saat aktivasi

---

## 6. Troubleshooting

### Aplikasi tidak bisa dibuka
- Pastikan Windows Defender/antivirus tidak memblokir file `.exe`
- Jalankan sebagai Administrator (right-click → "Run as administrator")
- Cek apakah komputer memenuhi spesifikasi minimum (Windows 10+, 4GB RAM, 500MB disk space)

### Browser tidak terbuka saat eksekusi
- Pastikan folder `_internal` tidak dihapus/dipindah
- Cek folder `logs` untuk error log

### Error saat aktivasi lisensi
- Pastikan komputer memiliki koneksi internet saat aktivasi pertama
- Jika offline mode, lisensi tetap berjalan dengan cache yang ada
- Fingerprint hardware akan di-generate otomatis saat pertama kali dijalankan

---

## 7. Update Aplikasi

Jika ada update versi baru:
1. Build ulang `.exe` dengan `python build_exe.py`
2. Buat file ZIP baru dengan versi yang baru
3. Kirim ke customer untuk replace folder `AutomationStudio` yang lama
4. **Penting:** Minta customer backup folder `workflows` dan `data` sebelum update

---

## 8. Catatan Lisensi

- Setiap aktivasi lisensi akan bind ke 1 komputer (hardware fingerprint)
- Mode Free: 10 data/hari, unlimited days
- Mode Licensed: unlimited data, unlimited days
- Customer perlu aktivasi lisensi via dialog License di aplikasi
- Server verifikasi: `https://id.gmteknologi.com/modules/addons/superpos_license/lib/LicenseAPI.php`

---

## 9. Kontak Support

Jika customer mengalami masalah:
1. Minta screenshot error message
2. Minta file log dari folder `logs/`
3. Cek folder `screenshots/` untuk visual evidence error

---

**Build terakhir:** 10 Juni 2026  
**Versi Aplikasi:** 1.0.0  
**Platform:** Windows 10/11 (64-bit)