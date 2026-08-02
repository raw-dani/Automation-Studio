# 📋 RINCIAN BIAYA PEMBUATAN APLIKASI AUTOMATION STUDIO (PENGERJAAN INDIVIDU / FREELANCER)

**Nama Aplikasi:** Automation Studio (RPA - Robotic Process Automation)
**Lokasi Pengembangan:** Indonesia
**Model Pengerjaan:** Individu / Freelancer (Full-Stack Developer)
**Estimasi Durasi:** ± 5 Bulan (110 Hari Kerja Efektif)

---

## 1. RINGKASAN EKSEKUTIF

| Item | Nilai |
|------|-------|
| Total Biaya Pengembangan | **± Rp 95.000.000** |
| Estimasi Durasi Pengerjaan | ± 5 Bulan |
| Jumlah Modul Utama | 14 Modul |
| Tenaga | 1 Orang (Full-Stack Developer) |

### Perbandingan dengan Model Tim

| Model | Durasi | Total Biaya | Selisih |
|-------|--------|------------:|--------:|
| Tim / Vendor (7-8 orang) | ± 4 Bulan | ± Rp 155.000.000 | - |
| **Individu / Freelancer** | **± 5 Bulan** | **± Rp 95.000.000** | **Hemat ± Rp 60.000.000 (39%)** |

---

## 2. ASUMSI BIAYA (RATE FREELANCER INDONESIA)

| Level Freelancer | Rate/Jam | Rate/Hari (8 jam) | Rate/Bulan (22 hari) |
|------------------|---------:|------------------:|---------------------:|
| Junior Freelancer (1-3 th) | Rp 60.000 - 100.000 | Rp 480.000 - 800.000 | Rp 10.500.000 - 17.600.000 |
| **Middle Freelancer (3-5 th)** | **Rp 100.000 - 150.000** | **Rp 800.000 - 1.200.000** | **Rp 17.600.000 - 26.400.000** |
| Senior Freelancer (5+ th) | Rp 150.000 - 250.000 | Rp 1.200.000 - 2.000.000 | Rp 26.400.000 - 44.000.000 |

> **Asumsi yang digunakan:** Middle Freelancer Full-Stack dengan pengalaman 3-5 tahun menguasai Python, Desktop App (PyQt/PySide), RPA, OCR/Computer Vision, dan API.
> **Rate dipakai: Rp 800.000/hari** (tarif kompetitif freelance Indonesia untuk keahlian RPA + CV + Desktop App).

---

## 3. RINCIAN BIAYA PER MODUL (PENGERJAAN INDIVIDU)

### MODUL 1 - Analisis Kebutuhan & Perancangan Arsitektur
**Output:** Dokumen Requirements, Desain Arsitektur, Blueprint Modul

| Detail | Nilai |
|--------|-------|
| SDM | Individu (Developer) |
| Durasi | 4 Hari |
| Perhitungan | 4 hari × Rp 800.000 |
| **Biaya** | **Rp 3.200.000** |

---

### MODUL 2 - Core Workflow Engine (Backend Engine)
**File:** `backend/core/` (engine.py, workflow_parser.py, action_registry.py)

| Detail | Nilai |
|--------|-------|
| Output | Mesin eksekusi workflow, parser JSON, registry aksi |
| Kompleksitas | Tinggi - jantung sistem RPA |
| SDM | Individu (Developer) |
| Durasi | 14 Hari |
| Perhitungan | 14 hari × Rp 800.000 |
| **Biaya** | **Rp 11.200.000** |

---

### MODUL 3 - Modul Aksi / Actions (11 Jenis Aksi)
**File:** `backend/actions/` (click, input_text, dropdown, select2, radio, wait, loop, if_else, parallel_group, upload_file, base_action)

| Detail | Nilai |
|--------|-------|
| Output | 11 action class siap pakai |
| Kompleksitas | Menengah - handling selector & error tiap aksi |
| SDM | Individu (Developer) |
| Durasi | 16 Hari |
| Perhitungan | 16 hari × Rp 800.000 |
| **Biaya** | **Rp 12.800.000** |

---

### MODUL 4 - Frontend: Workflow Editor (Canvas & Designer)
**File:** `frontend/ui/` (workflow_editor.py, action_palette.py, properties_panel.py, main_window.py)

| Detail | Nilai |
|--------|-------|
| Output | Editor drag-and-drop workflow, palet aksi, panel properti |
| Kompleksitas | Tinggi - UX editor visual + desain UI (tanpa UI/UX terpisah) |
| SDM | Individu (Developer + UI/UX sekaligus) |
| Durasi | 18 Hari |
| Perhitungan | 18 hari × Rp 800.000 |
| **Biaya** | **Rp 14.400.000** |

---

### MODUL 5 - Modul Sumber Data (Data Source Connector)
**File:** `backend/data_sources/` (excel_source.py, csv_source.py, database_source.py, api_source.py)

| Detail | Nilai |
|--------|-------|
| Output | Konektor Excel, CSV, Database, dan REST API |
| Kompleksitas | Menengah |
| SDM | Individu (Developer) |
| Durasi | 7 Hari |
| Perhitungan | 7 hari × Rp 800.000 |
| **Biaya** | **Rp 5.600.000** |

---

### MODUL 6 - Modul Detector & OCR / Computer Vision
**File:** `backend/detectors/` (ocr_detector.py, image_detector.py, base_detector.py)

| Detail | Nilai |
|--------|-------|
| Output | Deteksi elemen UI via gambar + OCR untuk aplikasi legacy |
| Kompleksitas | Sangat Tinggi - riset CV, tuning akurasi OCR |
| SDM | Individu (Developer + riset AI) |
| Durasi | 14 Hari |
| Perhitungan | 14 hari × Rp 800.000 |
| **Biaya** | **Rp 11.200.000** |

---

### MODUL 7 - Frontend: Monitoring & Execution Panel
**File:** `frontend/ui/` (monitoring_panel.py, execution_panel.py) + `backend/monitoring/`

| Detail | Nilai |
|--------|-------|
| Output | Panel runtime monitoring, logger, screenshot, progress tracker, resume handler |
| Kompleksitas | Menengah |
| SDM | Individu (Developer) |
| Durasi | 6 Hari |
| Perhitungan | 6 hari × Rp 800.000 |
| **Biaya** | **Rp 4.800.000** |

---

### MODUL 8 - Modul Data Source Manager (Frontend)
**File:** `frontend/ui/data_source_manager.py`

| Detail | Nilai |
|--------|-------|
| Output | Manajemen koneksi & mapping sumber data dari UI |
| Kompleksitas | Menengah |
| SDM | Individu (Developer) |
| Durasi | 4 Hari |
| Perhitungan | 4 hari × Rp 800.000 |
| **Biaya** | **Rp 3.200.000** |

---

### MODUL 9 - REST API & Integrasi
**File:** `backend/api/` (routes.py, schemas.py)

| Detail | Nilai |
|--------|-------|
| Output | REST API untuk kontrol eksekusi, status, integrasi eksternal |
| Kompleksitas | Menengah |
| SDM | Individu (Developer) |
| Durasi | 5 Hari |
| Perhitungan | 5 hari × Rp 800.000 |
| **Biaya** | **Rp 4.000.000** |

---

### MODUL 10 - Build, Packaging & Deployment
**File:** `build_exe.py`, `main.py`, `config.yaml`

| Detail | Nilai |
|--------|-------|
| Output | Aplikasi desktop siap install (EXE), konfigurasi, build automation |
| Kompleksitas | Menengah |
| SDM | Individu (Developer) |
| Durasi | 4 Hari |
| Perhitungan | 4 hari × Rp 800.000 |
| **Biaya** | **Rp 3.200.000** |

---

### MODUL 11 - Pengujian (Testing & Debugging)
**Fase:** Unit Test, Integration Test, Regression Test, UAT

| Detail | Nilai |
|--------|-------|
| Output | Test case, laporan bug, hasil testing seluruh modul |
| Kompleksitas | Menengah - dilakukan mandiri tanpa QA terpisah |
| SDM | Individu (Developer + QA sekaligus) |
| Durasi | 6 Hari |
| Perhitungan | 6 hari × Rp 800.000 |
| **Biaya** | **Rp 4.800.000** |

---

### MODUL 12 - Dokumentasi & User Guide
**File:** `README.md`, `USER_GUIDE.md`, `PROJECT_PLAN.md`, `CHANGE_LOG.md`

| Detail | Nilai |
|--------|-------|
| Output | Panduan pengguna, dokumentasi teknis, panduan instalasi |
| SDM | Individu (Developer + Technical Writer sekaligus) |
| Durasi | 3 Hari |
| Perhitungan | 3 hari × Rp 800.000 |
| **Biaya** | **Rp 2.400.000** |

---

### MODUL 13 - Deployment, Training & Pendampingan
**Fase:** Instalasi di lingkungan user, pelatihan operator, pendampingan

| Detail | Nilai |
|--------|-------|
| Output | Aplikasi ter-deploy + 2 sesi training + pendampingan 1 bulan |
| SDM | Individu (Developer + Trainer sekaligus) |
| Durasi | 4 Hari |
| Perhitungan | 4 hari × Rp 800.000 |
| **Biaya** | **Rp 3.200.000** |

---

### MODUL 14 - Manajemen Proyek & Komunikasi Klien
**Fase:** Sepanjang proyek (koordinasi, pelaporan progress mingguan)

| Detail | Nilai |
|--------|-------|
| Output | Pelaporan progress, koordinasi dengan klien, manajemen perubahan |
| SDM | Individu (Developer + PM sekaligus) |
| Durasi | 5 Hari (berjalan bersamaan, bukan tambahan) |
| Perhitungan | ± 5% dari total biaya development |
| **Biaya** | **± Rp 4.000.000** |

---

## 4. REKAPITULASI BIAYA PER MODUL (INDIVIDU)

| No | Modul | Durasi Efektif (Hari) | Peran | Biaya |
|----|-------|:---------------------:|-------|------:|
| 1 | Analisis & Perancangan Arsitektur | 4 | Developer | Rp 3.200.000 |
| 2 | Core Workflow Engine | 14 | Developer | Rp 11.200.000 |
| 3 | Modul Aksi (11 Aksi) | 16 | Developer | Rp 12.800.000 |
| 4 | Frontend Workflow Editor | 18 | Developer + UI/UX | Rp 14.400.000 |
| 5 | Modul Sumber Data | 7 | Developer | Rp 5.600.000 |
| 6 | Modul Detector & OCR (CV) | 14 | Developer + AI Riset | Rp 11.200.000 |
| 7 | Monitoring & Execution Panel | 6 | Developer | Rp 4.800.000 |
| 8 | Data Source Manager (UI) | 4 | Developer | Rp 3.200.000 |
| 9 | REST API & Integrasi | 5 | Developer | Rp 4.000.000 |
| 10 | Build, Packaging & Deployment | 4 | Developer | Rp 3.200.000 |
| 11 | Pengujian (QA mandiri) | 6 | Developer + QA | Rp 4.800.000 |
| 12 | Dokumentasi & User Guide | 3 | Developer + Writer | Rp 2.400.000 |
| 13 | Deployment, Training & Pendampingan | 4 | Developer + Trainer | Rp 3.200.000 |
| 14 | Manajemen Proyek (±5%) | 5 | Developer + PM | ± Rp 4.000.000 |
| | **TOTAL** | **± 110 Hari** | **1 Orang** | **± Rp 88.000.000** |

> **Catatan:** Durasi efektif memperhitungkan pengerjaan paralel/bercampur antar modul yang saling terkait (misal modul 7, 8, 9 dikerjakan bersamaan dengan backend). Manajemen proyek (modul 14) berjalan berbarengan, **bukan penambahan hari kerja** — dihitung sebagai alokasi waktu ±5% dari keseluruhan.

### Estimasi Waktu (Jadwal 5 Bulan)

| Bulan | Modul yang Dikerjakan | Akumulasi Hari |
|-------|----------------------|:--------------:|
| Bulan 1 | Modul 1, 2 (Analisis + Core Engine) | 22 hari |
| Bulan 2 | Modul 3, 5 (Aksi + Sumber Data) | 22 hari |
| Bulan 3 | Modul 4, 8 (Editor + Data Source UI) | 22 hari |
| Bulan 4 | Modul 6, 7, 9 (OCR + Monitoring + API) | 22 hari |
| Bulan 5 | Modul 10, 11, 12, 13 (Build + Test + Dokumen + Training) | 22 hari |
| | **TOTAL** | **110 hari** |

---

### Biaya Non-Development (Estimasi)

| Item | Biaya |
|------|------:|
| Lisensi Software (Python, Tesseract OCR, DB - Open Source) | Rp 0 |
| Perangkat & Listrik selama dev | Rp 2.000.000 |
| Biaya komunikasi / internet | Rp 1.000.000 |
| **Subtotal Non-Development** | **± Rp 3.000.000** |

---

### 💰 GRAND TOTAL (PENGERJAAN INDIVIDU)

| Komponen | Nominal |
|----------|---------|
| Total Biaya Development (110 hari × Rp 800.000) | ± Rp 88.000.000 |
| Total Biaya Non-Development | ± Rp 3.000.000 |
| **GRAND TOTAL** | **± Rp 91.000.000** |
| **Dibulatkan (dengan buffer 5%)** | **± Rp 95.000.000** |

---

## 5. PERBANDINGAN BIAYA TIM vs INDIVIDU

| Aspek | Model Tim (7-8 orang) | Model Individu (1 orang) |
|-------|---------------------:|-------------------------:|
| Total Biaya | ± Rp 155.000.000 | ± Rp 95.000.000 |
| Durasi | ± 4 Bulan | ± 5 Bulan |
| Kecepatan Pengerjaan | Tinggi (paralel) | Sedang (berurutan/parsial) |
| Kualitas UI/UX | Tinggi (designer khusus) | Menengah (developer rangkap) |
| Kualitas Testing | Tinggi (QA khusus) | Menengah (test mandiri) |
| Risiko | Rendah (ada back-up SDM) | Sedang (single point of failure) |
| Komunikasi | Butuh koordinasi tim | Langsung ke klien |
| **Cocok untuk** | **Proyek enterprise / skala besar** | **Proyek UMKM / internal / budget terbatas** |

---

## 6. SKEMA PEMBAYARAN (SARAN - INDIVIDU)

| Termin | Tahapan | Persentase | Nominal |
|--------|---------|:----------:|--------:|
| Termin 1 | DP Penandatanganan Kontrak & Analysis (Modul 1) | 30% | Rp 28.500.000 |
| Termin 2 | Core Engine + Aksi + Sumber Data (Modul 2,3,5) | 30% | Rp 28.500.000 |
| Termin 3 | Editor + Monitoring + OCR + API (Modul 4,6,7,8,9) | 25% | Rp 23.750.000 |
| Termin 4 | Build, Testing, Deployment & Training (Modul 10-13) | 15% | Rp 14.250.000 |
| | **TOTAL** | **100%** | **Rp 95.000.000** |

---

## 7. OPSI PAKET BIAYA (INDIVIDU)

| Paket | Ruang Lingkup | Biaya | Durasi |
|-------|---------------|------:|--------|
| 🟢 **Basic** | Core Engine + 5 Aksi utama + Editor sederhana + Excel/CSV | Rp 40.000.000 - 50.000.000 | ± 2,5 Bulan |
| 🟡 **Standard** | Semua modul lengkap + OCR + Database/API + Monitoring | Rp 85.000.000 - 95.000.000 | ± 5 Bulan |
| 🔴 **Premium** | Standard + Support 6 bulan + Perawatan & update | Rp 110.000.000 - 125.000.000 | ± 6 Bulan |

---

## 8. CATATAN & ASUMSI PENTING (PENGERJAAN INDIVIDU)

1. **Rate freelance Rp 800.000/hari** adalah tarif kompetitif untuk developer Indonesia middle-level dengan skill Python + RPA + Desktop App (PyQt) + OCR/Computer Vision. Rate ini setara ± Rp 17.600.000/bulan, di bawah gaji vendor karena tanpa overhead perusahaan.

2. **Satu orang menangani semua peran:** Developer, UI/UX Designer, QA, Technical Writer, Trainer, dan Project Manager. Ini yang membuat biaya lebih hemat ± 39% dibanding model tim.

3. **Durasi lebih lama (± 5 bulan vs 4 bulan)** karena semua modul dikerjakan bergantian oleh satu orang, bukan paralel oleh tim yang berbeda.

4. **Resiko utama:** Jika freelancer berhalangan (sakit, dll), proyek terhambat karena tidak ada back-up SDM. Disarankan ada **rider kontrak** untuk penyerahan source code bertahap (per tahap pembayaran).

5. **Harga sudah termasuk:** source code, hak cipta aplikasi, dokumentasi, pelatihan, dan garansi perbaikan bug 3 bulan.

6. **Belum termasuk:** biaya pengembangan workflow spesifik klien (dihitung per workflow ± Rp 2.000.000 - Rp 5.000.000 tergantung kompleksitas).

7. **Cocok untuk:** kantor/instansi dengan budget terbatas, proyek internal, atau UMKM. Untuk proyek enterprise dengan kebutuhan tinggi dan deadline ketat, tetap disarankan model tim.

---

## 9. SKENARIO NEGOSIASI BIAYA (UNTUK PEMBELI)

| Skema | Total yang Dibayar | Cara Kerja |
|-------|-------------------:|------------|
| Borongan Tetap | Rp 90.000.000 - 95.000.000 | Harga final, selesai terima jadi |
| Per Tahap | Rp 88.000.000 (total dev) | Bayar per tahap modul selesai (skema di bawah) |
| Per Jam | Hitung ulang | Rate Rp 100.000/jam × estimasi 880-950 jam |

### Skenario Pembayaran Per Tahap (Bertahap)

| Tahap | Modul Selesai | Pembayaran |
|-------|---------------|-----------:|
| Tahap 1 | Analisis + Core Engine (Modul 1-2) | Rp 14.400.000 |
| Tahap 2 | Aksi + Sumber Data (Modul 3,5) | Rp 18.400.000 |
| Tahap 3 | Editor + UI (Modul 4,8) | Rp 17.600.000 |
| Tahap 4 | OCR + Monitoring + API (Modul 6,7,9) | Rp 20.000.000 |
| Tahap 5 | Build + Test + Docs + Training (Modul 10-13) | Rp 13.600.000 |
| Tahap 6 | Manajemen & Serah Terima (Modul 14) | Rp 4.000.000 |
| | **TOTAL** | **± Rp 88.000.000** |

---

*Dokumen disusun berdasarkan struktur modul aplikasi Automation Studio, dengan asumsi dikerjakan oleh 1 (satu) orang developer freelance di Indonesia. Estimasi bersifat indikatif dan dapat disesuaikan setelah scope & jadwal final disepakati.*