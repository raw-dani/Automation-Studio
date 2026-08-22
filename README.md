# Automation Studio

Aplikasi otomasi modular berbasis Python untuk otomatisasi workflow web, data processing, dan monitoring.

## Fitur

- **Workflow Builder** - Drag & drop action nodes dengan properties panel lengkap
- **Action Palette** - Sidebar terorganisir dengan kategori: Navigation, Input, Logic, Detection, Data
- **Execution Engine** - Playwright automation dengan retry otomatis, checkpoint, resume
- **Batch Input** - Isi banyak form field sekaligus via JavaScript untuk kecepatan maksimal
- **Select2 Support** - Native support untuk dropdown Select2 dengan fallback search
- **HTTP Submit** - Submit form via HTTP POST langsung, bypass UI click
- **Login dengan OTP** - Action khusus untuk login dengan verifikasi OTP, termasuk skip jika session masih valid
- **Data Source** - Excel, CSV, Database (MySQL/PostgreSQL/SQLite/MSSQL), REST API
- **Session Management** - 3 mode: default (fresh), persistent (save login), connect (CDP remote browser)
- **Monitoring** - Log, Screenshot saat error, Progress tracking, Failed rows dialog, Retry
- **License System** - Free mode (10 data/hari) + Licensed mode

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Bahasa | Python 3.10+ |
| Automation | Playwright |
| UI Desktop | PySide6 (Qt for Python) |
| API (opsional) | FastAPI + Uvicorn |
| OCR | pytesseract + Pillow |
| Image Detection | opencv-python + pyautogui |
| Excel/CSV | pandas + openpyxl |
| Database | SQLAlchemy |
| Config | PyYAML |
| Logging | loguru |

## Struktur Proyek

```
Automation Studio/
├── backend/
│   ├── core/          # Core engine (workflow parser, action registry, execution engine)
│   ├── actions/       # Actions (click, input_text, input_date, batch_input, select2, http_submit, login_otp, dll)
│   ├── data_sources/  # Data sources (Excel, CSV, Database, API)
│   ├── monitoring/    # Monitoring (log, screenshot, progress, resume)
│   ├── detectors/     # Detectors (OCR, Image Detection)
│   ├── license/       # License manager + usage tracker
│   └── api/           # FastAPI endpoints (opsional)
├── frontend/          # PySide6 UI
│   └── ui/            # UI components (action palette, properties panel, execution panel, workflow editor)
├── workflows/         # Penyimpanan workflow JSON
├── data/              # Contoh data source
├── logs/              # Log output
├── screenshots/       # Screenshot error
├── checkpoints/       # Checkpoint untuk resume
├── main.py            # Entry point
├── config.yaml        # Konfigurasi global
└── requirements.txt   # Dependencies
```

## Daftar Action Tersedia

### Navigation
- `click` - Klik elemen
- `navigate` - Buka URL
- `wait` - Tunggu kondisi tertentu

### Input
- `input_text` - Input teks
- `input_date` - Input tanggal dengan format khusus
- `select` - Pilih dari daftar opsi
- `select2` - Support dropdown Select2
- `select_dropdown` - Pilih dari dropdown standar
- `radio_select` - Pilih radio button
- `upload_file` - Upload file
- `http_submit` - Submit form via HTTP POST
- `batch_input` - Isi banyak field sekaligus via JS
- `otp_challenge` - Challenge OTP dengan modal browser
- `login_otp` - Login lengkap + OTP + skip jika session valid

### Logic
- `loop` - Loop dengan count/data_source/while
- `if_else` - Percabangan kondisi
- `parallel_group` - Eksekusi paralel child steps

### Data (placeholder)
- `extract` - Ekstrak data dari halaman
- `transform` - Transformasi data

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Browser

```bash
python -m playwright install chromium
```

### 3. Jalankan Aplikasi

```bash
python main.py
```

### 4. Jalankan Workflow (CLI)

```bash
# Validasi workflow
python -X utf8 main.py validate workflows/sample_workflow.json

# List semua workflow
python -X utf8 main.py list

# Jalankan workflow
python -X utf8 main.py run workflows/sample_workflow.json
```

## Format Workflow JSON

Workflow disimpan dalam format JSON dan bisa dibuat/diedit tanpa menyentuh kode.

```json
{
  "id": "workflow_001",
  "name": "Nama Workflow",
  "version": "1.0",
  "url": "https://example.com/login",
  "data_source": {
    "type": "none",
    "config": {}
  },
  "steps": [
    {
      "id": "step_1",
      "type": "navigate",
      "label": "Buka halaman login",
      "params": {
        "url": "https://example.com/login",
        "wait_until": "domcontentloaded",
        "timeout": 30000
      },
      "on_error": "stop",
      "retry": {
        "max_retries": 3,
        "delay": 2000
      }
    },
    {
      "id": "step_2",
      "type": "login_otp",
      "label": "Login dengan OTP",
      "params": {
        "username_selector": "#username",
        "username_value": "{{data.USERNAME}}",
        "password_selector": "#password",
        "password_value": "{{data.PASSWORD}}",
        "login_selector": "#btn-login",
        "check_selector": "#dashboard-welcome",
        "timeout": 30000,
        "wait_for_otp_timeout": 120000
      },
      "on_error": "stop",
      "retry": {
        "max_retries": 3,
        "delay": 2000
      }
    }
  ],
  "monitoring": {
    "screenshot_on_error": true,
    "screenshot_on_step": false,
    "log_level": "INFO"
  }
}
```

### Contoh Batch Input

```json
{
  "id": "step_batch",
  "type": "batch_input",
  "label": "Isi form pemilik",
  "params": {
    "fields": {
      "#frmPemohonNonDukcapil #tNIK": "{{data.NIK}}",
      "#frmPemohonNonDukcapil #tNAMA_LENGKAP": "{{data.NAMA}}",
      "#frmPemohonNonDukcapil #tALAMAT": "{{data.ALAMAT}}"
    },
    "clear_first": true,
    "wait_after": 100,
    "timeout": 10000,
    "trigger_events": true
  }
}
```

## Workflow Terupload

- `workflows/login_with_otp.json` - Contoh workflow login dengan OTP
- `workflows/MelengkapiBerkasGU.json` - Workflow pengisian formulir tanah
- `workflows/MelengkapiBidangTanah.json` - Workflow pengisian data bidang tanah
- `workflows/isi_data_pelanggan.json` - Workflow input data pelanggan
- `workflows/import_produk_superpos.json` - Workflow import produk

## Session Management

Engine mendukung 3 mode session:

| Mode | Deskripsi |
|------|-----------|
| `default` | Browser baru setiap eksekusi |
| `persistent` | Simpan session ke folder lokal, login 1x reuse selamanya |
| `connect` | Hubungkan ke browser Chrome/Edge yang sudah running via CDP |

Untuk login dengan OTP, gunakan action `login_otp` dengan parameter `check_selector`. Jika session masih valid, action akan otomatis skip login.

## Lisensi

- **Free Mode**: 10 data per hari, cocok untuk testing
- **Licensed Mode**: Tanpa batasan, aktivasi via License Key

Lihat `frontend/ui/license_dialog.py` untuk detail aktivasi.

## Development

### Menambah Action Baru

1. Buat file di `backend/actions/` (extend `BaseAction`)
2. Daftarkan di `main.py` dan semua registry di frontend
3. Tambahkan ke `VALID_ACTIONS` di `backend/core/workflow_parser.py`
4. Tambahkan icon + kategori di `frontend/ui/action_palette.py`
5. Tambahkan form fields di `frontend/ui/properties_panel.py`

Lihat [PROJECT_PLAN.md](PROJECT_PLAN.md) untuk dokumentasi lengkap arsitektur dan tahapan pengembangan.

## Phase Saat Ini

**Phase 1: Foundation** ✅ Selesai
- Setup project structure
- Core engine (workflow parser, action registry, execution engine)
- 16 Actions (Click, Input Text, Input Date, Select, Select2, Select Dropdown, Radio Select, Upload File, HTTP Submit, Wait, Loop, If Else, Parallel Group, Batch Input, OTP Challenge, Login OTP, Navigate)
- Playwright integration
- Config & logging
- License system
- Session management
- UI lengkap (Action Palette, Properties Panel, Execution Panel, Workflow Editor, Data Source Manager)

**Phase 2-5:** Lihat [PROJECT_PLAN.md](PROJECT_PLAN.md)

## Lisensi

Proyek internal untuk keperluan otomatisasi.
