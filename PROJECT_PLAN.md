# 🏗️ Automation Studio - Project Plan

> **Deskripsi:** Aplikasi otomasi modular berbasis Python untuk otomatisasi workflow web, data processing, dan monitoring.

---

## 📋 Daftar Isi

- [Arsitektur](#-arsitektur)
- [Struktur Proyek](#-struktur-proyek)
- [Komponen Utama](#-komponen-utama)
- [Workflow JSON Format](#-workflow-json-format)
- [Tech Stack](#-tech-stack)
- [Tahapan Implementasi](#-tahapan-implementasi)
- [Keunggulan Desain](#-keunggulan-desain)

---

## 🧩 Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (PySide6)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Workflow     │  │ Action       │  │ Properties       │  │
│  │ Editor       │  │ Palette      │  │ Panel            │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Data Source  │  │ Execution    │  │ Monitoring       │  │
│  │ Manager      │  │ Panel        │  │ Panel            │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ API (FastAPI - Opsional)
┌───────────────────────▼─────────────────────────────────────┐
│                      BACKEND                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    CORE ENGINE                        │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │ Workflow   │  │ Action       │  │ Execution    │ │   │
│  │  │ Parser     │  │ Registry     │  │ Engine       │ │   │
│  │  └────────────┘  └──────────────┘  └──────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   ACTIONS    │  │ DATA SOURCES │  │   MONITORING     │  │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────────┐  │  │
│  │  │ Click  │  │  │  │ Excel  │  │  │  │ Log        │  │  │
│  │  ├────────┤  │  │  ├────────┤  │  │  ├────────────┤  │  │
│  │  │Input   │  │  │  │ CSV    │  │  │  │ Screenshot │  │  │
│  │  │ Text   │  │  │  ├────────┤  │  │  ├────────────┤  │  │
│  │  ├────────┤  │  │  │Database│  │  │  │ Progress   │  │  │
│  │  │Select  │  │  │  ├────────┤  │  │  ├────────────┤  │  │
│  │  │Dropdown│  │  │  │ API    │  │  │  │ Resume     │  │  │
│  │  ├────────┤  │  │  └────────┘  │  │  └────────────┘  │  │
│  │  │Upload  │  │  └──────────────┘  └──────────────────┘  │
│  │  │ File   │  │                                           │
│  │  ├────────┤  │  ┌────────────────────────────────────┐  │
│  │  │ Wait   │  │  │          DETECTORS                 │  │
│  │  ├────────┤  │  │  ┌────────────┐  ┌──────────────┐  │  │
│  │  │ Loop   │  │  │  │ OCR        │  │ Image        │  │  │
│  │  ├────────┤  │  │  │ Detector   │  │ Detection    │  │  │
│  │  │If Else │  │  │  └────────────┘  └──────────────┘  │  │
│  │  └────────┘  │  └────────────────────────────────────┘  │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktur Proyek

```
Automation Studio/
│
├── backend/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py              # Execution engine utama
│   │   ├── workflow_parser.py     # Parse workflow dari JSON
│   │   └── action_registry.py     # Registry semua action
│   │
│   ├── actions/
│   │   ├── __init__.py
│   │   ├── base_action.py         # Base class untuk semua action
│   │   ├── click_action.py
│   │   ├── input_text_action.py
│   │   ├── select_dropdown_action.py
│   │   ├── upload_file_action.py
│   │   ├── wait_action.py
│   │   ├── loop_action.py
│   │   └── if_else_action.py
│   │
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── base_source.py         # Base class untuk data source
│   │   ├── excel_source.py
│   │   ├── csv_source.py
│   │   ├── database_source.py
│   │   └── api_source.py
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── screenshot.py
│   │   ├── progress_tracker.py
│   │   └── resume_handler.py
│   │
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── base_detector.py
│   │   ├── ocr_detector.py
│   │   └── image_detector.py
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py              # FastAPI endpoints
│       └── schemas.py             # Pydantic models
│
├── frontend/
│   ├── __init__.py
│   ├── main.py                    # Entry point PySide6
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── workflow_editor.py     # Visual workflow builder
│   │   ├── action_palette.py      # Daftar action yang tersedia
│   │   ├── properties_panel.py    # Konfigurasi tiap action
│   │   ├── data_source_manager.py
│   │   ├── execution_panel.py
│   │   └── monitoring_panel.py
│   │
│   └── resources/
│       ├── __init__.py
│       ├── icons/
│       └── styles/
│
├── workflows/                     # Folder penyimpanan workflow JSON
│   └── .gitkeep
│
├── data/                          # Contoh data source
│   └── .gitkeep
│
├── logs/                          # Log output
│   └── .gitkeep
│
├── screenshots/                   # Screenshot error
│   └── .gitkeep
│
├── requirements.txt
├── config.yaml                    # Konfigurasi global
├── PROJECT_PLAN.md                # File ini
└── README.md
```

---

## 🧩 Komponen Utama

### 1. Core Engine (`backend/core/`)

| Modul | Fungsi |
|-------|--------|
| `engine.py` | Menjalankan workflow step-by-step, handle retry & resume |
| `workflow_parser.py` | Membaca & memvalidasi workflow JSON |
| `action_registry.py` | Mendaftarkan semua action agar bisa dipanggil secara dinamis |

### 2. Actions (`backend/actions/`)

Setiap action adalah class terpisah dengan interface seragam:

```python
class BaseAction:
    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        pass
```

| Action | Deskripsi |
|--------|-----------|
| **Click** | Klik elemen berdasarkan selector (CSS/XPath/Text) |
| **Input Text** | Mengetik teks ke input field |
| **Select Dropdown** | Memilih opsi dropdown |
| **Upload File** | Upload file via file input |
| **Wait** | Wait (fixed time, until visible, until hidden) |
| **Loop** | Iterasi berdasarkan data source atau kondisi |
| **If Else** | Conditional branching berdasarkan kondisi |

### 3. Data Sources (`backend/data_sources/`)

Interface seragam untuk membaca data:

```python
class BaseDataSource:
    def read(self, config: dict) -> DataIterator:
        pass
```

| Data Source | Library |
|-------------|---------|
| **Excel** | `openpyxl` / `pandas` |
| **CSV** | `csv` / `pandas` |
| **Database** | `SQLAlchemy` (support MySQL, PostgreSQL, SQLite) |
| **API** | `httpx` / `requests` |

### 4. Execution Engine (`backend/core/engine.py`)

| Fitur | Teknologi |
|-------|-----------|
| **Browser Automation** | Playwright (Chromium, Firefox, WebKit) |
| **OCR** | `pytesseract` + `Pillow` untuk membaca teks dari gambar |
| **Image Detection** | `opencv-python` / `pyautogui` untuk deteksi elemen visual |
| **Retry Otomatis** | Exponential backoff dengan konfigurasi max retry |

### 5. Monitoring (`backend/monitoring/`)

| Modul | Fungsi |
|-------|--------|
| **Logger** | Logging terstruktur (file + console) menggunakan `loguru` |
| **Screenshot** | Otomatis screenshot saat error |
| **Progress Tracker** | Track progress per step (completed/total) |
| **Resume Handler** | Simpan state workflow, bisa dilanjutkan jika gagal |

### 6. Frontend PySide6 (`frontend/`)

| Panel | Fungsi |
|-------|--------|
| **Workflow Editor** | Drag & drop action nodes, connect secara visual |
| **Action Palette** | Sidebar berisi daftar action yang bisa ditambahkan |
| **Properties Panel** | Konfigurasi parameter tiap action |
| **Data Source Manager** | Kelola koneksi data source |
| **Execution Panel** | Start/Stop/Pause workflow, lihat real-time progress |
| **Monitoring Panel** | Lihat log, screenshot error, history eksekusi |

### 7. API Layer (Opsional - untuk akses web via FastAPI)

| Endpoint | Fungsi |
|----------|--------|
| `POST /workflow/run` | Jalankan workflow |
| `GET /workflow/status/{id}` | Cek status eksekusi |
| `POST /workflow/stop/{id}` | Hentikan eksekusi |
| `GET /logs/{execution_id}` | Ambil log |
| `GET /screenshots/{execution_id}` | Ambil screenshot |

---

## 📋 Workflow JSON Format

```json
{
  "id": "workflow_001",
  "name": "Input Customer Data",
  "version": "1.0",
  "data_source": {
    "type": "excel",
    "config": {
      "file_path": "data/customers.xlsx",
      "sheet": "Sheet1"
    }
  },
  "steps": [
    {
      "id": "step_1",
      "type": "click",
      "label": "Klik tombol Tambah",
      "params": {
        "selector": "#btn-add",
        "selector_type": "css",
        "wait_before": 1000
      },
      "on_error": "stop",
      "retry": {
        "max_retries": 3,
        "delay": 2000
      }
    },
    {
      "id": "step_2",
      "type": "input_text",
      "label": "Isi Nama",
      "params": {
        "selector": "#input-name",
        "value": "{{data.nama}}",
        "clear_first": true
      }
    },
    {
      "id": "step_3",
      "type": "if_else",
      "label": "Cek jenis kelamin",
      "condition": {
        "variable": "{{data.jenis_kelamin}}",
        "operator": "equals",
        "value": "Laki-laki"
      },
      "then": [
        {
          "id": "step_3a",
          "type": "select_dropdown",
          "params": {
            "selector": "#gender",
            "value": "L"
          }
        }
      ],
      "else": [
        {
          "id": "step_3b",
          "type": "select_dropdown",
          "params": {
            "selector": "#gender",
            "value": "P"
          }
        }
      ]
    }
  ],
  "monitoring": {
    "screenshot_on_error": true,
    "screenshot_on_step": false,
    "log_level": "INFO"
  }
}
```

### Penjelasan Field:

| Field | Deskripsi |
|-------|-----------|
| `id` | Unique identifier workflow |
| `name` | Nama workflow |
| `version` | Versi workflow |
| `data_source` | Konfigurasi sumber data (Excel/CSV/DB/API) |
| `steps` | Array of step objects |
| `steps[].id` | Unique identifier step |
| `steps[].type` | Tipe action (click, input_text, dll) |
| `steps[].label` | Label untuk ditampilkan di UI |
| `steps[].params` | Parameter spesifik untuk action |
| `steps[].on_error` | Aksi saat error: `stop`, `skip`, `retry` |
| `steps[].retry` | Konfigurasi retry (max_retries, delay) |
| `{{data.field}}` | Variable substitution dari data source |

---

## 🛠️ Tech Stack

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| **Bahasa** | Python | 3.10+ |
| **Automation** | Playwright | Latest |
| **UI Desktop** | PySide6 (Qt for Python) | 6.x |
| **API (opsional)** | FastAPI + Uvicorn | Latest |
| **OCR** | pytesseract + Pillow | Latest |
| **Image Detection** | opencv-python + pyautogui | Latest |
| **Excel/CSV** | pandas + openpyxl | Latest |
| **Database** | SQLAlchemy + databases | 2.x |
| **HTTP Client** | httpx | Latest |
| **Config** | PyYAML | Latest |
| **Logging** | loguru | Latest |
| **Packaging** | PyInstaller | Latest |

---

## 🚀 Tahapan Implementasi

### ✅ Phase 1: Foundation (Minggu 1) ✅ SELESAI

**Tujuan:** Setup project dan implementasi core engine dengan 3 action dasar.

- [x] Setup project structure & virtual environment
- [x] Buat `requirements.txt` dengan semua dependencies
- [x] Implementasi `base_action.py` (Base class untuk semua action)
- [x] Implementasi `action_registry.py` (Registry pattern)
- [x] Implementasi `workflow_parser.py` (Parse & validasi JSON)
- [x] Implementasi `engine.py` (Execution engine dengan Playwright)
- [x] Implementasi 3 action dasar:
  - [x] `click_action.py`
  - [x] `input_text_action.py`
  - [x] `wait_action.py`
- [x] Simpan & load workflow JSON dari folder `workflows/`
- [x] Buat `config.yaml` untuk konfigurasi global
- [x] Testing dasar: validasi workflow berhasil

### ✅ Phase 2: Actions & Data Sources (Minggu 2) ✅ SELESAI

**Tujuan:** Melengkapi semua action dan integrasi data source.

- [x] Implementasi `select_dropdown_action.py`
- [x] Implementasi `upload_file_action.py`
- [x] Implementasi `loop_action.py`
- [x] Implementasi `if_else_action.py`
- [x] Implementasi `base_source.py` (Base class data source)
- [x] Implementasi `excel_source.py` (baca data dari Excel)
- [x] Implementasi `csv_source.py` (baca data dari CSV)
- [x] Variable substitution system (`{{data.field}}`)
- [x] Error handling & retry mechanism
- [x] Testing: workflow dengan loop & data source berhasil

### ✅ Phase 3: Monitoring & Detection (Minggu 3) ✅ SELESAI

**Tujuan:** Sistem monitoring lengkap dan deteksi visual.

- [x] Implementasi `logger.py` (loguru integration + structured JSON logs)
- [x] Implementasi `screenshot.py` (screenshot otomatis saat error)
- [x] Implementasi `progress_tracker.py` (track progress per step with callback)
- [x] Implementasi `resume_handler.py` (save & resume checkpoint ke file)
- [x] Implementasi `ocr_detector.py` (pytesseract integration, dukung eng+ind)
- [x] Implementasi `image_detector.py` (opencv template matching + color detection)
- [x] Testing: semua module monitoring & detection berhasil di-load

### ✅ Phase 4: Frontend PySide6 (Minggu 4-5) ✅ SELESAI

**Tujuan:** Membangun antarmuka desktop yang lengkap.

- [x] Setup PySide6 project
- [x] Implementasi `main_window.py` (main window & layout dengan splitter)
- [x] Implementasi `workflow_editor.py` (drag & drop nodes, connections, zoom, grid)
- [x] Implementasi `action_palette.py` (sidebar action list by category)
- [x] Implementasi `properties_panel.py` (konfigurasi action dengan form dinamis)
- [x] Implementasi `data_source_manager.py` (kelola Excel/CSV data source + preview)
- [x] Implementasi `execution_panel.py` (start/stop/pause dengan worker thread)
- [x] Implementasi `monitoring_panel.py` (log viewer, screenshot list, summary)
- [x] Integrasi frontend dengan backend engine via signals/slots
- [x] Testing: semua frontend module berhasil di-load

### ✅ Phase 5: Advanced & Polish (Minggu 6) ✅ SELESAI

**Tujuan:** Fitur lanjutan dan persiapan distribusi.

- [x] Implementasi `database_source.py` (SQLAlchemy integration - MySQL/PostgreSQL/SQLite)
- [x] Implementasi `api_source.py` (httpx integration - REST API dengan pagination)
- [x] Implementasi FastAPI backend (`api/routes.py` + `schemas.py`)
- [x] Export/Import workflow (JSON file via UI)
- [x] Build .exe dengan PyInstaller (script siap)
- [x] Dokumentasi (README.md lengkap)
- [x] Final testing & debugging (semua module verified)
- [x] User acceptance test

---

## 💡 Keunggulan Desain

| Keunggulan | Deskripsi |
|------------|-----------|
| **✅ Modular** | Setiap action, data source, dan detector adalah plugin terpisah |
| **✅ Konfigurasi-driven** | Workflow dibuat via JSON, bukan kode |
| **✅ Extensible** | Tambah action baru cukup buat class baru di folder `actions/` |
| **✅ Resumable** | Workflow bisa dilanjutkan dari step terakhir jika gagal |
| **✅ Multi-source** | Bisa gabung data dari Excel, CSV, DB, dan API |
| **✅ Dual Interface** | Desktop (PySide6) + API (FastAPI) untuk integrasi sistem lain |
| **✅ Visual Builder** | Drag & drop workflow editor tanpa coding |
| **✅ Monitoring** | Log real-time, screenshot error, progress tracking |

---

## 📊 Progress Tracker

| Phase | Status | Target Selesai |
|-------|--------|----------------|
| **Phase 1: Foundation** | ✅ Selesai | Minggu 1 |
| **Phase 2: Actions & Data Sources** | ✅ Selesai | Minggu 2 |
| **Phase 3: Monitoring & Detection** | ✅ Selesai | Minggu 3 |
| **Phase 4: Frontend PySide6** | ✅ Selesai | Minggu 4-5 |
| **Phase 5: Advanced & Polish** | ✅ Selesai | Minggu 6 |

---

> **Catatan:** Dokumen ini akan diperbarui seiring perkembangan proyek. Setiap perubahan arsitektur atau penambahan fitur baru akan dicatat di sini.