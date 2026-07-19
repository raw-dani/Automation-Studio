# Automation Studio

Aplikasi otomasi modular berbasis Python untuk otomatisasi workflow web, data processing, dan monitoring.

## Fitur

- **Workflow Builder** - Drag & drop action nodes (Click, Input Text, Select Dropdown, Upload File, Wait, Loop, If Else)
- **Data Source** - Excel, CSV, Database, API
- **Execution Engine** - Playwright automation, OCR, Image Detection, Retry otomatis
- **Monitoring** - Log, Screenshot saat error, Progress tracking, Resume jika gagal

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
│   ├── actions/       # Actions (click, input_text, wait, dll)
│   ├── data_sources/  # Data sources (Excel, CSV, Database, API)
│   ├── monitoring/    # Monitoring (log, screenshot, progress, resume)
│   ├── detectors/     # Detectors (OCR, Image Detection)
│   └── api/           # FastAPI endpoints (opsional)
├── frontend/          # PySide6 UI (masih dalam pengembangan)
│   └── ui/            # UI components
├── workflows/         # Penyimpanan workflow JSON
├── data/              # Contoh data source
├── logs/              # Log output
├── screenshots/       # Screenshot error
├── main.py            # Entry point
├── config.yaml        # Konfigurasi global
└── requirements.txt   # Dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Browser

```bash
python -m playwright install chromium
```

### 3. Jalankan Workflow

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
      "label": "Klik tombol",
      "params": {
        "selector": "#btn-add",
        "selector_type": "css"
      }
    }
  ]
}
```

Lihat [PROJECT_PLAN.md](PROJECT_PLAN.md) untuk dokumentasi lengkap arsitektur dan tahapan pengembangan.

## Phase Saat Ini

**Phase 1: Foundation** ✅ Selesai
- Setup project structure
- Core engine (workflow parser, action registry, execution engine)
- 3 Action dasar (Click, Input Text, Wait)
- Playwright integration
- Config & logging

**Phase 2-5:** Lihat [PROJECT_PLAN.md](PROJECT_PLAN.md)

## Lisensi

Proyek internal untuk keperluan otomatisasi.