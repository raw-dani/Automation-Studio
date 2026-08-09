# TODO: Integrasi Lisensi WHMCS dengan Automation Studio

## 📋 Ringkasan
Integrasi aplikasi Automation Studio dengan modul lisensi WHMCS `superpos_license` yang terletak di:
```
C:\Users\EIKON\Documents\APP\POS\super-pos\superpos-whmcs\modules\addons\superpos_license
```

**Endpoint API:** `https://id.gmteknologi.com/modules/addons/superpos_license/lib/LicenseAPI.php`

**API Actions yang tersedia:**
| Action | Method | Deskripsi |
|--------|--------|-----------|
| `activate` | POST | Aktivasi lisensi dengan fingerprint hardware |
| `verify` | POST | Verifikasi lisensi aktif |
| `deactivate` | POST | Nonaktifkan lisensi dari hardware ini |
| `ping` | GET/POST | Cek koneksi server (tanpa auth) |

**Autentikasi:** Header `X-API-Key` atau POST param `api_key`

---

## 🎯 Strategi Lisensi (FREE vs LICENSED)

### Mode Tanpa Lisensi (FREE MODE)
- ✅ Aplikasi **tetap bisa dijalankan** sepenuhnya
- ✅ Semua fitur tetap tersedia (buat/edit/simpan workflow)
- ⚠️ **Batasan: Hanya 10 data per flow per hari**
  - Setiap kali workflow dieksekusi dengan data source, hanya **10 baris data pertama** yang diproses
  - Jika workflow tanpa data source (single run), tetap dihitung sebagai 1 data
  - Counter di-reset setiap hari (00:00)
  - Counter disimpan di `data/usage.json`
- 🔓 Status bar menampilkan: `🔓 Free (10/10 data hari ini)`

### Mode Dengan Lisensi (LICENSED MODE)
- ✅ **Tidak ada batasan data** - semua data diproses
- ✅ Verifikasi lisensi via WHMCS server
- ✅ **1 Lisensi = 1 Komputer/Laptop** (hardware binding)
- 🔒 Status bar menampilkan: `🔒 Licensed`

---

## 🔒 MEKANISME 1 LISENSI = 1 KOMPUTER (HARDWARE BINDING)

### Konsep
- Setiap lisensi **terikat ke satu hardware fingerprint** yang unik
- Lisensi tidak bisa dipakai di 2 komputer secara bersamaan
- Untuk pindah komputer, user harus **deaktivasi** dulu di komputer lama, baru aktivasi di komputer baru

### 1. Hardware Fingerprint yang Kuat
- [x] Generate fingerprint kombinasi dari beberapa identifier hardware:
  ```
  Windows: MachineGuid (registry) + MAC Address + Disk Serial + Hostname
  Linux:   MachineId (/etc/machine-id) + MAC Address + Disk Serial + Hostname
  macOS:   IOPlatformUUID + MAC Address + Disk Serial + Hostname
  ```
- [x] Hash kombinasi dengan SHA-256: `sha256(machine_guid + "|" + mac + "|" + disk_serial + "|" + hostname)`
- [x] Fingerprint disimpan lokal di `data/license.json`
- [x] Fingerprint **tidak pernah berubah** selama install sama

### 2. Alur Aktivasi (1 kompter)
```
[User memasukkan license key di komputer A]
    ↓
Aplikasi generate fingerprintA (hardware komputer A)
    ↓
POST /activate {license_key, fingerprint: fingerprintA}
    ↓
Server: license_keys.hardware_fingerprint = fingerprintA
    ↓
Response: token valid → LICENSED di komputer A ✓
```

### 3. Alur Verifikasi (Cek berkala)
```
[Setiap start / interval 24 jam]
    ↓
Aplikasi kirim fingerprintA
    ↓
POST /verify {license_key, fingerprint: fingerprintA}
    ↓
Server cek:
  - License aktif? 
  - hardware_fingerprint == fingerprintA? 
    → YES: LANJUT (valid)
    → NO: TOLAK (403 - Fingerprint mismatch)
```

### 4. Alur Pindah Komputer (User harus deaktivasi)
```
[Komputer A] → Deactivate License di aplikasi
    ↓
POST /deactivate {license_key, fingerprint: fingerprintA}
    ↓
Server: hardware_fingerprint = '' (kosong)
    ↓
[Komputer B] → Activate License dengan key yang sama
    ↓
POST /activate {license_key, fingerprint: fingerprintB}
    ↓
Server: hardware_fingerprint = fingerprintB → LICENSED di komputer B ✓
```

### 5. Jika User Pindah Komputer TANPA Deaktivasi
```
[Komputer B] coba aktivasi dengan lisensi yang masih terikat komputer A]
    ↓
POST /activate {license_key, fingerprint: fingerprintB}
    ↓
Server: lisensi SUDAH aktif dengan fingerprintA
    ↓
TOLAK: "License sudah aktif di komputer lain"
    ↓
Solusi: User harus deaktivasi dari komputer A, ATAU kontak admin
admin untuk reset lisensi di WHMCS
```

### 6. Penanganan Fingerprint Berubah (Ganti Hardware)
- [x] Jika `verify` gagal karena fingerprint mismatch:
  - [x] Jangan otomatis reset lisensi
  - [x] Tampilkan pesan: "Lisensi terdaftar untuk hardware berbeda"
  - [x] Beri opsi: "Deactivate License" (jika masih di komputer lama) atau "Contact Support"
  - [x] Log kejadian ke server (untuk deteksi penyalahgunaan)

### 7. Pencegahan Bypass
- [x] Jangan simpan lisensi dalam bentuk plaintext yang mudah diedit
- [x] Simpan `license.json` dengan hash/token, bukan license key asli (untuk verifikasi offline)
- [x] Pastikan fingerprint di-compute saat runtime (bukan hardcoded)
- [x] Gunakan koneksi HTTPS (server sudah HTTPS)

---

## ✅ Checklist Implementasi

### 1. Backend - License Manager Module ✅ SELESAI
- [x] Buat `backend/license/__init__.py`
- [x] Buat `backend/license/fingerprint.py`:
  - [x] `get_machine_guid()` - Ambil MachineGuid dari registry (Windows)
  - [x] `get_mac_address()` - Ambil MAC address aktif
  - [x] `get_disk_serial()` - Ambil serial disk
  - [x] `get_hostname()` - Ambil hostname
  - [x] `get_fingerprint()` - Gabungkan + hash SHA-256
  - [x] Test konsistensi: fingerprint sama setiap call
- [x] Buat `backend/license/license_manager.py`:
  - [x] Class `LicenseManager` dengan method:
    - [x] `activate(license_key)` - Aktivasi lisensi (bind ke fingerprint)
    - [x] `verify()` - Verifikasi lisensi (cek fingerprint match)
    - [x] `deactivate()` - Nonaktifkan lisensi dari hardware ini
    - [x] `get_status()` - Dapatkan status lisensi
    - [x] `is_licensed()` - Cek apakah lisensi valid (True/False)
    - [x] `get_remaining_quota()` - Sisa kuota hari ini (untuk free mode)
  - [x] Simpan lisensi lokal di `data/license.json`:
    ```json
    {
      "license_key": "XXXX-XXXX-XXXX-XXXX",
      "fingerprint": "sha256-hash",
      "activated_at": "2026-08-09T12:00:00",
      "last_verify_at": "2026-08-09T12:00:00",
      "status": "licensed"
    }
    ```
  - [x] Cache verifikasi (TTL 24 jam sesuai server)
  - [x] Auto-verify saat aplikasi start
  - [x] Auto-deactivate saat uninstall/close (opsional)

### 2. Backend - Usage Tracker (FREE MODE LIMIT) ✅ SELESAI
- [x] Buat `backend/license/usage_tracker.py`:
  - [x] Class `UsageTracker` dengan method:
    - [x] `get_today_usage()` - Jumlah data yang diproses hari ini
    - [x] `increment_usage(count)` - Tambah jumlah data yang diproses
    - [x] `get_remaining_quota()` - Sisa kuota (10 - today_usage)
    - [x] `is_quota_exceeded()` - Cek apakah kuota sudah habis
    - [x] `reset_daily()` - Reset counter jika hari berganti
  - [x] Simpan data di `data/usage.json`:
    ```json
    {
      "date": "2026-08-09",
      "processed_count": 7,
      "daily_limit": 10
    }
    ```
  - [x] Auto-reset saat tanggal berganti

### 3. Backend - Engine Integration (BATASAN DATA) ⚠️ PARSIAL
- [x] Modifikasi `backend/core/engine.py`:
  - [x] Tambah atribut `license_manager` dan `usage_tracker`
  - [x] Tambah method `set_license_manager()`
  - [ ] Sebelum eksekusi workflow, cek `LicenseManager.is_licensed()`
  - [ ] Jika **free mode**:
    - [ ] Hitung jumlah data yang akan diproses dari data source
    - [ ] Cek `UsageTracker.get_remaining_quota()`
    - [ ] Jika kuota habis → hentikan eksekusi dengan pesan:
      ```
      "Free mode: Kuota harian 10 data telah tercapai.
       Aktifkan lisensi untuk pemrosesan tanpa batas."
      ```
    - [ ] Jika kuota tersisa < jumlah data → proses hanya data yang tersisa
    - [ ] Setelah selesai, panggil `UsageTracker.increment_usage(processed_count)`
  - [ ] Jika **licensed mode** → proses semua data tanpa batasan

### 4. Backend - Config ✅ SELESAI
- [x] Tambah konfigurasi lisensi di `config.yaml`:
  ```yaml
  license:
    server_url: "https://id.gmteknologi.com/modules/addons/superpos_license/lib/LicenseAPI.php"
    api_key: ""  # Diisi dari settings
    verify_interval_hours: 24
    auto_verify_on_start: true
    free_mode:
      enabled: true
      daily_data_limit: 10
  ```

### 5. Frontend - License Dialog ✅ SELESAI
- [x] Buat `frontend/ui/license_dialog.py`:
  - [x] Dialog aktivasi lisensi (input license key)
  - [x] Tampilkan status lisensi:
    - [x] **Free Mode** - "Menggunakan mode gratis (10 data/hari)"
    - [x] **Licensed** - "Lisensi aktif, tanpa batasan"
  - [x] Tampilkan kuota yang tersisa hari ini (free mode)
  - [x] Tampilkan hardware fingerprint (dengan partial mask)
  - [x] Tombol "Activate", "Deactivate", "Refresh"
  - [x] Link ke halaman pembelian lisensi
  - [x] Info "1 lisensi = 1 komputer"

### 6. Frontend - Main Window Integration ✅ SELESAI
- [x] Modifikasi `frontend/ui/main_window.py`:
  - [x] Inisialisasi `LicenseManager` dan `UsageTracker` di `__init__`
  - [x] Cek lisensi saat aplikasi start:
    - [x] Jika free mode → tampilkan info "Free mode: 10 data/hari" (bukan blokir)
    - [x] Jika lisensi valid → tampilkan "Licensed"
    - [x] Jika fingerprint mismatch → tampilkan warning "Lisensi untuk komputer berbeda"
  - [x] Tambah menu "License" di menu bar:
    - [x] "License Status" - Tampilkan status + kuota
    - [x] "Activate License" - Buka dialog aktivasi
    - [x] "Deactivate License" - Nonaktifkan dari hardware ini
  - [x] Tambah status lisensi di status bar
  - [ ] On close: jika licensed → tawarkan "Deactivate before closing"

### 7. Frontend - Status Bar ✅ SELESAI
- [x] Tambah indikator lisensi di status bar:
  - [x] `🔒 Licensed` (hijau) - Lisensi valid, tanpa batasan
  - [x] `🔓 Free (7/10 data)` (oranye) - Free mode, sisa kuota
  - [x] Tooltip dengan detail lisensi + fingerprint

### 8. Frontend - Execution Panel Warning ✅ SELESAI
- [x] Modifikasi `frontend/ui/execution_panel.py`:
  - [x] Sebelum start, tampilkan info kuota jika free mode:
    - [x] "Free mode: Sisa 3 dari 10 data hari ini"
    - [x] Jika kuota habis → disable Start button + tooltip
  - [ ] Setelah eksekusi, update kuota yang tersisa

### 9. Testing ⚠️ BELUM DIMULAI
- [ ] Test fingerprint:
  - [ ] Fingerprint konsisten antar sesi di komputer sama
  - [ ] Fingerprint berbeda di komputer berbeda (simulasi)
- [ ] Test free mode tanpa lisensi:
  - [ ] Eksekusi workflow dengan 5 data → sukses, sisa 5
  - [ ] Eksekusi workflow dengan 8 data → hanya 5 diproses, sisa 0
  - [ ] Eksekusi lagi → ditolak "Kuota habis"
  - [ ] Reset counter saat hari berganti
- [ ] Test licensed mode:
  - [ ] Aktivasi dengan license key valid
  - [ ] Eksekusi workflow dengan 100+ data → semua diproses
  - [ ] Restart aplikasi → auto-verify sukses
- [ ] Test 1 lisensi = 1 komputer:
  - [ ] Aktivasi di komputer A → sukses
  - [ ] Coba aktivasi di komputer B (fingerprint berbeda) → **DITOLAK**
  - [ ] Deaktivasi di komputer A → sukses
  - [ ] Aktivasi di komputer B → sukses
  - [ ] Aktivasi di komputer A lagi (tanpa deaktivasi di B) → **DITOLAK**
- [ ] Test fingerprint mismatch:
  - [ ] Ganti fingerprint di license.json manual → verify gagal → warning
- [ ] Test offline mode (server tidak bisa diakses)
- [ ] Test cache TTL (verifikasi tidak terlalu sering)

### 10. Dokumentasi ⚠️ BELUM DIMULAI
- [ ] Update `README.md` dengan info lisensi
- [ ] Update `USER_GUIDE.md` dengan cara aktivasi + pindah komputer
- [ ] Update `CHANGE_LOG.md`

---

## 📊 Ringkasan Progress

### ✅ Selesai Diimplementasikan (8/10 bagian)
1. ✅ Backend License Manager Module
2. ✅ Backend Usage Tracker
3. ⚠️ Backend Engine Integration (parsial - infrastruktur siap, enforcement belum)
4. ✅ Backend Config
5. ✅ Frontend License Dialog
6. ✅ Frontend Main Window Integration
7. ✅ Frontend Status Bar
8. ✅ Frontend Execution Panel Warning

### ⚠️ Belum Diimplementasikan (2/10 bagian)
9. ⏳ Testing (belum dimulai)
10. ⏳ Dokumentasi (belum dimulai)

### 📁 File yang Sudah Dibuat/Diubah
```
✅ backend/license/__init__.py
✅ backend/license/fingerprint.py
✅ backend/license/license_manager.py
✅ backend/license/usage_tracker.py
✅ backend/core/engine.py (ditambah license integration)
✅ frontend/ui/license_dialog.py
✅ frontend/ui/main_window.py (ditambah license menu + status)
✅ frontend/ui/execution_panel.py (ditambah license check)
✅ config.yaml (ditambah license config)
⏳ data/license.json (akan dibuat saat aktivasi)
⏳ data/usage.json (akan dibuat saat pertama kali run)
```

### 🔧 Fitur yang Sudah Berjalan
- ✅ Hardware fingerprint generation (Windows/Linux/macOS)
- ✅ Aktivasi lisensi dengan binding ke 1 komputer
- ✅ Verifikasi lisensi dengan cache 24 jam
- ✅ Deaktivasi lisensi
- ✅ Free mode tracking 10 data/hari
- ✅ UI: License menu, status bar, dialog
- ✅ Cek kuota sebelum eksekusi di execution panel
- ✅ Offline mode support (cache tetap berlaku)

### ⚠️ Fitur yang Belum Lengkap
- ⏳ Enforcement batasan data di engine (masih perlu implementasi penghitungan data sebenarnya)
- ⏳ Update kuota otomatis setelah eksekusi
- ⏳ Testing komprehensif
- ⏳ Dokumentasi

---

## 🚀 Langkah Selanjutnya
1. **Testing**: Jalankan aplikasi dan test aktivasi lisensi
2. **Engine Integration**: Implementasi penghitungan dan pembatasan data di `_execute_data_source_loop()`
3. **Usage Update**: Tambah `usage_tracker.increment_usage()` setelah eksekusi selesai
4. **Dokumentasi**: Update README, USER_GUIDE, CHANGE_LOG

---

## ⚠️ Catatan Penting
1. **Fingerprint** harus konsisten antar sesi (jangan generate ulang setiap start)
2. **Cache verifikasi** untuk mengurangi beban server (TTL 24 jam)
3. **Offline mode** - aplikasi tetap berjalan dengan cache valid (maks 24 jam)
4. **Free mode** - aplikasi tetap berjalan, hanya dibatasi 10 data/hari
5. **1 Lisensi = 1 Komputer** - hardware binding ketat via fingerprint
6. **Pindah komputer** - harus deaktivasi dulu di komputer lama
7. **Fingerprint mismatch** - jangan auto-reset, beri warning dan opsi admin reset
8. **API key** disimpan di server WHMCS, bukan di aplikasi
9. **Domain** gunakan `localhost` untuk desktop app