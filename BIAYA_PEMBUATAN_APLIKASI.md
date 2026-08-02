# 📋 RINCIAN BIAYA PEMBUATAN APLIKASI AUTOMATION STUDIO

**Nama Aplikasi:** Automation Studio (RPA - Robotic Process Automation)
**Lokasi Pengembangan:** Indonesia
**Estimasi Durasi:** ± 4 Bulan (88 Hari Kerja)

---

## 1. RINGKASAN EKSEKUTIF

| Item | Nilai |
|------|-------|
| Total Biaya Pengembangan | **± Rp 145.000.000 - Rp 155.000.000** |
| Estimasi Durasi Pengerjaan | ± 4 Bulan |
| Jumlah Modul Utama | 14 Modul |
| Tim yang Dibutuhkan | 7-8 Orang (Developers, AI Engineer, UI/UX, QA, PM) |

---

## 2. ASUMSI BIAYA (RATE TENAGA AHLI DI INDONESIA)

Rate dihitung berdasarkan standar gaji bulanan (22 hari kerja) + margin vendor/kontraktor:

| Posisi | Gaji Std/Bulan | Rate/Hari Kerja | Rate/Bulan (Vendor) |
|--------|---------------|-----------------|---------------------|
| Junior Developer | Rp 5.000.000 | Rp 350.000 | Rp 7.700.000 |
| Middle Developer | Rp 10.000.000 - 15.000.000 | Rp 700.000 | Rp 15.400.000 |
| Senior Developer | Rp 18.000.000 - 25.000.000 | Rp 1.150.000 | Rp 25.300.000 |
| AI/ML Engineer (Senior) | Rp 20.000.000 - 28.000.000 | Rp 1.200.000 | Rp 26.400.000 |
| UI/UX Designer | Rp 8.000.000 - 12.000.000 | Rp 550.000 | Rp 12.100.000 |
| QA Engineer | Rp 7.000.000 - 9.000.000 | Rp 400.000 | Rp 8.800.000 |
| Technical Writer | Rp 6.000.000 - 8.000.000 | Rp 350.000 | Rp 7.700.000 |
| Project Manager | Rp 15.000.000 - 25.000.000 | Rp 900.000 | Rp 19.800.000 |
| Business Analyst | Rp 8.000.000 - 12.000.000 | Rp 500.000 | Rp 11.000.000 |

---

## 3. RINCIAN BIAYA PER MODUL

### MODUL 1 - Analisis Kebutuhan & Perancangan Arsitektur
**Fase:** Discovery, Requirement Gathering, Desain Arsitektur Sistem

| Detail | Nilai |
|--------|-------|
| Output | Dokumen Requirements, Diagram Arsitektur, Blueprint Modul |
| SDM | Business Analyst + Senior Developer |
| Durasi | 5 Hari |
| Perhitungan | 5 hari × (Rp 500.000 + Rp 1.150.000) |
| **Biaya** | **Rp 8.250.000** |

---

### MODUL 2 - Core Workflow Engine (Backend Engine)
**File:** `backend/core/` (engine.py, workflow_parser.py, action_registry.py)

| Detail | Nilai |
|--------|-------|
| Output | Mesin eksekusi workflow, parser JSON workflow, registry 11+ aksi terdaftar |
| Kompleksitas | Tinggi - jantung sistem RPA |
| SDM | Senior Developer |
| Durasi | 15 Hari |
| Perhitungan | 15 hari × Rp 1.150.000 |
| **Biaya** | **Rp 17.250.000** |

---

### MODUL 3 - Modul Aksi / Actions (11 Jenis Aksi)
**File:** `backend/actions/` (click, input_text, dropdown, select2, radio, wait, loop, if_else, parallel_group, upload_file, base_action)

| Detail | Nilai |
|--------|-------|
| Output | 11 action class siap pakai: Click, Input Teks, Dropdown, Select2, Radio, Wait, Loop, If-Else, Group Paralel, Upload File, Base Action |
| Kompleksitas | Menengah - masing-masing aksi butuh handling selector & error |
| SDM | Middle Developer |
| Durasi | 20 Hari |
| Perhitungan | 20 hari × Rp 700.000 |
| **Biaya** | **Rp 14.000.000** |

---

### MODUL 4 - Frontend: Workflow Editor (Canvas & Designer)
**File:** `frontend/ui/` (workflow_editor.py, action_palette.py, properties_panel.py, main_window.py)

| Detail | Nilai |
|--------|-------|
| Output | Editor drag-and-drop workflow, palet aksi, panel properti, jendela utama |
| Kompleksitas | Tinggi - UX editor visual seperti UiPath Studio |
| SDM | Middle Developer + UI/UX Designer |
| Durasi | 25 Hari (Dev) + 8 Hari (UI/UX) |
| Perhitungan | 25 × Rp 700.000 + 8 × Rp 550.000 |
| **Biaya** | **Rp 21.900.000** |

---

### MODUL 5 - Modul Sumber Data (Data Source Connector)
**File:** `backend/data_sources/` (excel_source.py, csv_source.py, database_source.py, api_source.py)

| Detail | Nilai |
|--------|-------|
| Output | Konektor Excel, CSV, Database, dan REST API |
| Kompleksitas | Menengah - konektor & mapping data |
| SDM | Middle Developer |
| Durasi | 12 Hari |
| Perhitungan | 12 hari × Rp 700.000 |
| **Biaya** | **Rp 8.400.000** |

---

### MODUL 6 - Modul Detector & OCR / Computer Vision
**File:** `backend/detectors/` (ocr_detector.py, image_detector.py, base_detector.py)

| Detail | Nilai |
|--------|-------|
| Output | Deteksi elemen UI via gambar + pengenalan teks (OCR) untuk aplikasi legacy |
| Kompleksitas | Sangat Tinggi - membutuhkan riset CV, tuning akurasi OCR |
| SDM | AI/ML Engineer (Senior) |
| Durasi | 25 Hari |
| Perhitungan | 25 hari × Rp 1.200.000 |
| **Biaya** | **Rp 30.000.000** |

---

### MODUL 7 - Frontend: Monitoring & Execution Panel
**File:** `frontend/ui/` (monitoring_panel.py, execution_panel.py) + `backend/monitoring/`

| Detail | Nilai |
|--------|-------|
| Output | Panel runtime monitoring, panel eksekusi, logger, screenshot, progress tracker, resume handler |
| Kompleksitas | Menengah |
| SDM | Middle Developer |
| Durasi | 10 Hari |
| Perhitungan | 10 hari × Rp 700.000 |
| **Biaya** | **Rp 7.000.000** |

---

### MODUL 8 - Modul Data Source Manager (Frontend)
**File:** `frontend/ui/data_source_manager.py`

| Detail | Nilai |
|--------|-------|
| Output | Manajemen koneksi & mapping sumber data dari UI |
| Kompleksitas | Menengah |
| SDM | Middle Developer |
| Durasi | 5 Hari |
| Perhitungan | 5 hari × Rp 700.000 |
| **Biaya** | **Rp 3.500.000** |

---

### MODUL 9 - REST API & Integrasi
**File:** `backend/api/` (routes.py, schemas.py)

| Detail | Nilai |
|--------|-------|
| Output | REST API untuk kontrol eksekusi, status, dan integrasi sistem eksternal |
| Kompleksitas | Menengah |
| SDM | Middle Developer |
| Durasi | 8 Hari |
| Perhitungan | 8 hari × Rp 700.000 |
| **Biaya** | **Rp 5.600.000** |

---

### MODUL 10 - Build, Packaging & Deployment
**File:** `build_exe.py`, `main.py`, `config.yaml`

| Detail | Nilai |
|--------|-------|
| Output | Aplikasi desktop siap install (EXE), konfigurasi, build automation |
| Kompleksitas | Menengah - setup PyInstaller & dependency |
| SDM | Middle Developer |
| Durasi | 6 Hari |
| Perhitungan | 6 hari × Rp 700.000 |
| **Biaya** | **Rp 4.200.000** |

---

### MODUL 11 - Pengujian QA (Quality Assurance)
**Fase:** Unit Test, Integration Test, Regression Test, UAT

| Detail | Nilai |
|--------|-------|
| Output | Test case, laporan bug, sertifikasi kualitas aplikasi |
| SDM | QA Engineer |
| Durasi | 15 Hari |
| Perhitungan | 15 hari × Rp 400.000 |
| **Biaya** | **Rp 6.000.000** |

---

### MODUL 12 - Dokumentasi & User Guide
**File:** `README.md`, `USER_GUIDE.md`, `PROJECT_PLAN.md`, `CHANGE_LOG.md`

| Detail | Nilai |
|--------|-------|
| Output | Panduan pengguna, dokumentasi teknis, panduan instalasi |
| SDM | Technical Writer |
| Durasi | 5 Hari |
| Perhitungan | 5 hari × Rp 350.000 |
| **Biaya** | **Rp 1.750.000** |

---

### MODUL 13 - Deployment, Training & Pendampingan
**Fase:** Instalasi di lingkungan user, pelatihan operator, masa pendampingan

| Detail | Nilai |
|--------|-------|
| Output | Aplikasi ter-deploy + 2 sesi training + pendampingan 1 bulan |
| SDM | Middle Developer (Trainer) |
| Durasi | 5 Hari (Training) |
| Perhitungan | 5 hari × Rp 700.000 |
| **Biaya** | **Rp 3.500.000** |

---

### MODUL 14 - Manajemen Proyek (Project Management)
**Fase:** Sepanjang proyek (koordinasi, sprint planning, pelaporan progress)

| Detail | Nilai |
|--------|-------|
| Output | Pelaporan mingguan, koordinasi tim, manajemen risiko |
| SDM | Project Manager |
| Durasi | 88 Hari |
| Perhitungan | 10% dari total biaya development |
| **Biaya** | **± Rp 13.200.000** |

---

## 4. REKAPITULASI BIAYA PER MODUL

| No | Modul | Durasi (Hari) | SDM | Biaya |
|----|-------|:-------------:|-----|------:|
| 1 | Analisis & Perancangan Arsitektur | 5 | BA + Senior Dev | Rp 8.250.000 |
| 2 | Core Workflow Engine | 15 | Senior Dev | Rp 17.250.000 |
| 3 | Modul Aksi (11 Aksi) | 20 | Middle Dev | Rp 14.000.000 |
| 4 | Frontend Workflow Editor | 25 + 8 | Middle Dev + UI/UX | Rp 21.900.000 |
| 5 | Modul Sumber Data | 12 | Middle Dev | Rp 8.400.000 |
| 6 | Modul Detector & OCR (CV) | 25 | AI/ML Senior | Rp 30.000.000 |
| 7 | Monitoring & Execution Panel | 10 | Middle Dev | Rp 7.000.000 |
| 8 | Data Source Manager (UI) | 5 | Middle Dev | Rp 3.500.000 |
| 9 | REST API & Integrasi | 8 | Middle Dev | Rp 5.600.000 |
| 10 | Build, Packaging & Deployment | 6 | Middle Dev | Rp 4.200.000 |
| 11 | Pengujian QA | 15 | QA Engineer | Rp 6.000.000 |
| 12 | Dokumentasi & User Guide | 5 | Technical Writer | Rp 1.750.000 |
| 13 | Deployment, Training & Pendampingan | 5 | Middle Dev | Rp 3.500.000 |
| 14 | Manajemen Proyek (10%) | 88 | Project Manager | ± Rp 13.200.000 |
| | **TOTAL** | **± 88 Hari** | **7-8 Orang** | **± Rp 144.550.000** |

### Biaya Non-Development (Estimasi)

| Item | Biaya |
|------|------:|
| Lisensi Software (Python, Tesseract OCR, DB - semuanya Open Source) | Rp 0 |
| Server / Hosting (jika perlu API server) | Rp 1.500.000/tahun |
| Biaya Operasional & Listrik selama dev | Rp 2.000.000 |
| **Subtotal Non-Development** | **± Rp 3.500.000** |

### 💰 GRAND TOTAL

| Komponen | Nominal |
|----------|---------|
| Total Biaya Development | ± Rp 144.550.000 |
| Total Biaya Non-Development | ± Rp 3.500.000 |
| **GRAND TOTAL** | **± Rp 148.000.000** |
| **Dibulatkan (dengan buffer 5%)** | **± Rp 155.000.000** |

---

## 5. OPSI PAKET BIAYA

| Paket | Ruang Lingkup | Biaya | Durasi |
|-------|---------------|------:|--------|
| 🟢 **Basic** | Core Engine + 5 Aksi utama + Editor sederhana + Excel/CSV | Rp 65.000.000 - 75.000.000 | ± 2 Bulan |
| 🟡 **Standard** | Semua modul lengkap + OCR + Database/API + Monitoring | Rp 145.000.000 - 155.000.000 | ± 4 Bulan |
| 🔴 **Premium/Enterprise** | Standard + Multi-user, AI planning, support 6 bulan, SLA | Rp 200.000.000 - 250.000.000 | ± 6 Bulan |

---

## 6. SKEMA PEMBAYARAN (SARAN)

| Termin | Tahapan | Persentase | Nominal |
|--------|---------|:----------:|--------:|
| Termin 1 | Penandatanganan Kontrak & Discovery | 30% | Rp 46.500.000 |
| Termin 2 | Prototype & Core Engine (Modul 2-4) | 30% | Rp 46.500.000 |
| Termin 3 | Modul Lengkap (Modul 5-10) | 25% | Rp 38.750.000 |
| Termin 4 | UAT, Deployment & Training (Modul 11-13) | 15% | Rp 23.250.000 |
| | **TOTAL** | **100%** | **Rp 155.000.000** |

> *Catatan: Nominal di atas berdasarkan paket Standard dan dapat disesuaikan berdasarkan negosiasi.*

---

## 7. CATATAN & ASUMSI PENTING

1. **Harga per modul** dihitung berdasarkan tingkat kompleksitas teknis masing-masing modul, bukan ukuran file/kode.
2. **Modul Detector & OCR** menjadi modul termahal karena membutuhkan keahlian khusus Computer Vision/AI dengan akurasi tinggi untuk mengenali elemen aplikasi legacy.
3. **Harga sudah termasuk:** source code, hak cipta aplikasi, dokumentasi, pelatihan, dan garansi pemeliharaan 3 bulan.
4. **Belum termasuk:** biaya pengembangan workflow spesifik klien (dihitung per workflow ± Rp 2.500.000 - Rp 7.500.000 tergantung kompleksitas).
5. **Nilai tukar & inflasi** dapat memengaruhi estimasi jika proyek berjalan lebih dari 6 bulan.
6. Estimasi mengikuti standar **rate vendor IT Indonesia** (Jakarta & sekitarnya). Untuk kota lain (Surabaya, Bandung, dll) bisa 10-15% lebih rendah, untuk vendor international +50-100%.

---

*Dokumen disusun berdasarkan struktur modul aplikasi Automation Studio yang telah dikembangkan. Estimasi bersifat indikatif dan dapat disesuaikan setelah scope final disepakati.*