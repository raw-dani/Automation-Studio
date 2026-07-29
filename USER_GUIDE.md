# 📖 Panduan Pengguna - Automation Studio

> **Versi:** 1.0.0  
> **Terakhir diperbarui:** Juli 2026  
> **Platform:** Windows 10/11

---

## 📋 Daftar Isi

1. [Apa itu Automation Studio?](#-apa-itu-automation-studio)
2. [Instalasi](#-instalasi)
3. [Konfigurasi Awal](#-konfigurasi-awal)
4. [Cara Penggunaan](#-cara-penggunaan)
5. [Membuat Workflow](#-membuat-workflow)
6. [Menjalankan Workflow](#-menjalankan-workflow)
7. [Monitoring & Troubleshooting](#-monitoring--troubleshooting)
8. [API Reference](#-api-reference)
9. [FAQ & Tips](#-faq--tips)

---

## Apa itu Automation Studio?

Automation Studio adalah aplikasi otomasi modular berbasis Python yang memungkinkan Anda membuat dan menjalankan workflow otomatisasi tanpa menulis kode. Mirip dengan Power Automate Desktop, tapi lebih ringan dan bisa disesuaikan dengan kebutuhan perusahaan Anda.

### 🎯 Fitur Utama

- ✅ **Visual Workflow Builder** - Drag & drop tanpa coding
- ✅ **10+ Actions** - Click, Input Text, Select Dropdown, Upload File, Wait, Loop, If Else, HTTP Submit, Radio Select, Parallel Group
- ✅ **Browser Session Reuse (CDP Detection)** - Detect running browsers with remote debugging to reuse existing login sessions
- ✅ **4 Data Sources** - Excel, CSV, Database (MySQL/PostgreSQL/SQLite), REST API
- ✅ **Monitoring Real-time** - Log, screenshot error, progress tracking
- ✅ **Resume on Failure** - Lanjutkan dari step terakhir jika gagal
- ✅ **OCR & Image Detection** - Baca teks dari gambar, deteksi elemen visual
- ✅ **Dual Interface** - Desktop GUI + REST API

---

## Instalasi

### 📦 Sistem Requirement

- **OS:** Windows 10/11 (64-bit)
- **RAM:** Minimal 4GB (disarankan 8GB)
- **Python:** 3.10 atau lebih tinggi
- **Tesseract OCR** (opsional): Download dari [GitHub](https://github.com/tesseract-ocr/tesseract)

### 🔧 Langkah Instalasi

#### 1. Clone/Download Project

```bash
# Jika menggunakan git
git clone <repository-url>
cd Automation Studio

# Atau extract ZIP file ke folder
```

#### 2. Buat Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Atau menggunakan PowerShell
.\venv\Scripts\Activate.ps1
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt

# Install playwright browsers
playwright install chromium firefox webkit
```

#### 4. Install Tesseract OCR (Opsional)

Untuk fitur OCR:
1. Download installer dari: https://github.com/tesseract-ocr/tesseract
2. Install di C:\Program Files\Tesseract-OCR\
3. Set environment variable:
   ```
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

---

## Konfigurasi Awal

### 1. File `config.yaml`

Buka file `config.yaml` dan sesuaikan dengan kebutuhan:

```yaml
# Konfigurasi Global
app_name: "Automation Studio"
version: "1.0.0"
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# Paths
paths:
  workflows: "workflows"
  data: "data"
  logs: "logs"
  screenshots: "screenshots"
  checkpoints: "checkpoints"

# Browser Settings
browser:
  headless: false  # true = tanpa GUI browser
  slow_mo: 0  # Delay antar action (ms)
  timeout: 30000  # Timeout default (ms)

# Default retry settings
retry:
  max_retries: 3
  delay: 2000  # ms
```

### 2. Folder Structure

Pastikan struktur folder seperti ini:

```
Automation Studio/
├── config.yaml          # Konfigurasi
├── workflows/           # Simpan workflow JSON
│   └── sample_workflow.json
├── data/                # Data source files
│   └── customers.xlsx
├── logs/                # Log executions
├── screenshots/         # Screenshot errors
└── checkpoints/         # Resume checkpoints
```

---

## Cara Penggunaan

Automation Studio bisa dijalankan dalam 3 mode:

### 🖥️ Mode 1: Desktop GUI (Recommended untuk pemula)

```bash
python frontend/main.py
```

**Fitur:**
- Visual drag & drop workflow editor
- Action palette dengan 7 actions
- Properties panel untuk konfigurasi
- Real-time monitoring panel
- Data source preview

### 💻 Mode 2: CLI (Command Line Interface)

```bash
# Bantuan
python -X utf8 main.py --help

# Validasi workflow
python -X utf8 main.py validate workflows/sample_workflow.json

# List semua actions
python -X utf8 main.py actions

# Preview Excel data
python -X utf8 main.py preview-excel --file data/customers.xlsx --sheet Sheet1

# Preview CSV data
python -X utf8 main.py preview-csv --file data/transactions.csv

# Jalankan workflow langsung
python -X utf8 main.py run --workflow workflows/sample_workflow.json
```

### 🌐 Mode 3: REST API Server

```bash
python -m uvicorn backend.api.routes:app --host 0.0.0.0 --port 8000 --reload
```

Akses documentation: http://localhost:8000/docs

---

### 🔍 Mode 4: Detect Browser & Reuse Session (CDP)

Jika Anda sudah login di browser dan ingin workflow menggunakan sesi login tersebut (tanpa perlu login ulang), gunakan fitur **Browser Detection**:

#### Syarat:
Browser harus dijalankan dengan flag **remote debugging**:
```bash
# Chrome
chrome.exe --remote-debugging-port=9222

# Edge
msedge.exe --remote-debugging-port=9222
```

#### Cara Menggunakan:
1. Buka browser Chrome/Edge yang sudah login
2. Pastikan browser berjalan dengan remote debugging port
3. Buka Automation Studio
4. Di panel **Execution**, klik tombol **🔍 Detect Browsers**
5. Browser yang terdeteksi akan muncul, dengan endpoint CDP-nya
6. Pilih browser yang terdeteksi → endpoint CDP otomatis terisi
7. Klik **Start** untuk menjalankan workflow

Workflow akan terhubung ke browser yang sudah login dan langsung menjalankan aksi tanpa perlu login ulang.

---

## Membuat Workflow

### 📝 Langkah-langkah:

#### 1. Buka Aplikasi

```bash
python frontend/main.py
```

#### 2. Buat Workflow Baru

- Klik menu **File → New Workflow** (atau Ctrl+N)
- Atau klik tombol **New** di toolbar

#### 3. Tambahkan Actions

**Cara 1: Drag & Drop**
1. Pilih action dari **Action Palette** (sebelah kiri)
2. Drag ke **Workflow Editor** (area tengah)
3. Drop di posisi yang diinginkan

**Cara 2: Double Click**
1. Double-click action di palette
2. Otomatis muncul di editor

#### 4. Konfigurasi Actions

1. **Klik** pada node action di editor
2. Atau **double-click** untuk edit properties
3. Isi parameter di **Properties Panel** (sebelah kanan):
   - **Label:** Nama yang deskriptif
   - **Selector:** CSS selector / XPath / Text
   - **Value:** Nilai input atau variabel (`{{data.field}}`)
   - **Retry:** Max retries dan delay

#### 5. Set Data Source (Opsional)

1. Buka **Data Source** panel (kanan bawah)
2. Pilih tipe: **None**, **Excel**, atau **CSV**
3. Browse file data source
4. Klik **Preview Data** untuk cek data
5. Referensikan field dengan `{{data.nama_field}}`

#### 6. Simpan Workflow

- Klik menu **File → Save** (Ctrl+S)
- Atau klik tombol **Save** di toolbar
- Pilih lokasi di folder `workflows/`

---

## Format Workflow JSON

Workflow disimpan dalam format JSON. Berikut contoh:

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
    }
  ],
  "monitoring": {
    "screenshot_on_error": true,
    "screenshot_on_step": false,
    "log_level": "INFO"
  }
}
```

### 📋 Field Explanation

| Field | Deskripsi | Contoh |
|-------|-----------|--------|
| `id` | Unique ID workflow | `workflow_001` |
| `name` | Nama workflow | `Input Customer Data` |
| `version` | Versi workflow | `1.0` |
| `data_source.type` | Tipe data source | `excel`, `csv`, `database`, `api` |
| `data_source.config` | Konfigurasi data source | `{"file_path": "...", "sheet": "Sheet1"}` |
| `steps[]` | Array of actions | - |
| `steps[].id` | Unique ID step | `step_1` |
| `steps[].type` | Tipe action | `click`, `input_text`, dll |
| `steps[].label` | Label untuk UI | `Klik tombol Tambah` |
| `steps[].params` | Parameter action | Lihat tabel di bawah |
| `steps[].on_error` | Aksi saat error | `stop`, `skip`, `retry` |
| `steps[].retry` | Retry config | `{"max_retries": 3, "delay": 2000}` |
| `{{data.field}}` | Variable substitution | `{{data.nama}}` |

### 🔧 Parameter per Action Type

#### Click
```json
{
  "selector": "#btn-submit",
  "selector_type": "css",  // css, xpath, text
  "wait_before": 1000      // ms
}
```

#### Input Text
```json
{
  "selector": "#username",
  "value": "{{data.username}}",  // atau text langsung
  "clear_first": true,
  "wait_before": 500
}
```

#### Select Dropdown
```json
{
  "selector": "#country",
  "select_by": "label",  // label, value, index
  "select_value": "Indonesia",
  "wait_before": 500
}
```

#### Upload File
```json
{
  "selector": "#file-input",
  "file_path": "{{data.document_path}}",
  "wait_before": 500
}
```

#### Wait
```json
{
  "wait_type": "until_visible",  // fixed, until_visible, until_hidden
  "selector": ".loading-spinner",
  "timeout": 10000  // ms
}
```

#### Loop
```json
{
  "loop_type": "data_source",  // count, data_source, while
  "count": 10,
  "data_source": "customers",
  "condition": "{{data.status}} == 'active'"
}
```

#### If Else
```json
{
  "condition": {
    "variable": "{{data.age}}",
    "operator": "greater_than",  // equals, not_equals, greater_than, less_than, contains
    "value": "18"
  },
  "then": [ /* steps jika true */ ],
  "else": [ /* steps jika false */ ]
}
```

---

## Menjalankan Workflow

### 🖥️ Dari GUI

1. **Buka workflow** yang ingin dijalankan
   - Menu **File → Open** (Ctrl+O)
   - Pilih file JSON workflow

2. **Klik tombol Start** (hijau) di panel **Execution**

3. **Pantau progress:**
   - Progress bar menunjukkan persentase
   - Tab **Monitoring** menampilkan log real-time
   - Screenshot otomatis jika error

4. **Kontrol:**
   - **Pause** - Jeda eksekusi
   - **Resume** - Lanjutkan
   - **Stop** - Hentikan sepenuhnya

### 💻 Dari CLI

```bash
python -X utf8 main.py run --workflow workflows/sample_workflow.json
```

### 🌐 Dari REST API

```bash
# POST http://localhost:8000/api/workflows/run
{
  "workflow_id": "workflow_001",
  "file_path": "workflows/sample_workflow.json"
}
```

Atau via Python:

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/workflows/run",
    json={
        "workflow_id": "workflow_001",
        "file_path": "workflows/sample_workflow.json"
    }
)

print(response.json())
```

---

## Monitoring & Troubleshooting

### 📊 Monitoring Panel (GUI)

Tab **Monitoring** menampilkan:

#### 1. Log Tab
- Waktu, level, step ID, dan pesan
- Warna berbeda per level:
  - 🔵 **INFO** - Informasi umum
  - 🟢 **SUCCESS** - Step berhasil
  - 🟡 **WARNING** - Peringatan
  - 🔴 **ERROR** - Error yang terjadi
  - ⚫ **DEBUG** - Detail debugging

#### 2. Screenshots Tab
- Daftar screenshot (error & step)
- Double-click untuk buka
- Klik **Refresh** untuk update list

#### 3. Summary Tab
- Status eksekusi
- Progress percentage
- Total steps (completed/failed/skipped)
- Duration

### 📁 Log Files

Semua log disimpan di folder `logs/`:

```
logs/
├── automation_studio_20260719.log      # Console log (loguru)
├── exec_abc123.jsonl                    # Execution log format JSONL
└── ...
```

#### Format JSONL (satu baris per log):

```json
{"timestamp": "2026-07-19T12:00:00", "level": "ERROR", "message": "Step failed", "execution_id": "abc123", "step_id": "step_1", "workflow_id": "wf_001", "data": {"error": "..."}}
```

### 🔍 Troubleshooting

#### Error: Playwright browser not found

```bash
playwright install
```

#### Error: Tesseract not found

Set environment variable:
```bash
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Atau tambahkan ke `config.yaml`:
```yaml
detectors:
  tesseract_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

#### Workflow gagal di step tertentu

1. Cek **Monitoring Panel** → **Log Tab** untuk error message
2. Cek **Screenshots Tab** untuk visual error
3. Gunakan **Resume** untuk lanjut dari step yang gagal
   - Workflow otomatis save checkpoint setiap step
   - Jika ada checkpoint, pilih **Resume** saat start

#### Import Error di PyInstaller build

Pastikan semua hidden imports terdaftar di `build_exe.py`:
```bash
python build_exe.py --cli
```

#### Database connection failed

Cek koneksi database:
```bash
# Test via CLI
python -X utf8 main.py test-db --dialect mysql --host localhost --database mydb --query "SELECT 1"
```

#### Browser Detection tidak menemukan browser

**Penyebab:** Browser tidak dijalankan dengan flag `--remote-debugging-port`.

**Solusi:**
1. Tutup semua instance Chrome/Edge
2. Buka browser dengan remote debugging port:
   ```bash
   # Chrome
   chrome.exe --remote-debugging-port=9222
   
   # Edge
   msedge.exe --remote-debugging-port=9222
   ```
3. Login ke aplikasi yang dituju
4. Kembali ke Automation Studio dan klik **🔍 Detect Browsers**

Atau, jika mengalami masalah dengan CDP detection:
- Pastikan tidak ada firewall yang memblokir localhost
- Coba port lain (9223, 9229) jika 9222 sibuk
- Cek apakah browser sudah benar-benar berjalan sebelum deteksi

#### Workflow gagal dengan HTTP 419 (CSRF mismatch)

Jika step `http_submit` gagal dengan error CSRF token mismatch:
- Pastikan form memiliki field `_token` yang ikut terkirim dalam POST body
- Cek apakah session cookie browser aktif dan valid

---

## API Reference

### Base URL

```
http://localhost:8000
```

### Endpoints

#### Health Check
```bash
GET /
GET /api/health
```

Response:
```json
{
  "status": "ok",
  "app_name": "Automation Studio",
  "version": "1.0.0",
  "timestamp": "2026-07-19T12:00:00"
}
```

#### List Workflows
```bash
GET /api/workflows
```

#### Get Workflow Detail
```bash
GET /api/workflows/{workflow_id}
```

#### Run Workflow
```bash
POST /api/workflows/run
Content-Type: application/json

{
  "workflow_id": "workflow_001",
  "file_path": "workflows/sample_workflow.json",
  "resume_from": "step_5"  // optional
}
```

#### Stop Workflow
```bash
POST /api/workflows/{workflow_id}/stop
```

#### Get Logs
```bash
GET /api/executions/{execution_id}/logs
```

#### Get Screenshots
```bash
GET /api/executions/{execution_id}/screenshots
```

#### Download Screenshot
```bash
GET /api/screenshots/{filename}
```

#### List Actions
```bash
GET /api/actions
```

Response:
```json
[
  {
    "name": "click",
    "description": "Click on element",
    "category": "Navigation"
  },
  // ...
]
```

#### Engine Status
```bash
GET /api/engine/status
```

### Contoh Penggunaan API

#### Python (httpx)

```python
import httpx

# 1. List workflows
response = httpx.get("http://localhost:8000/api/workflows")
workflows = response.json()

# 2. Run workflow
response = httpx.post(
    "http://localhost:8000/api/workflows/run",
    json={
        "workflow_id": "workflow_001",
        "file_path": "workflows/sample_workflow.json"
    }
)
result = response.json()
print(f"Execution ID: {result['execution_id']}")
print(f"Status: {result['status']}")

# 3. Get logs
logs = httpx.get(f"http://localhost:8000/api/executions/{result['execution_id']}/logs").json()
for log in logs:
    print(f"{log['level']}: {log['message']}")
```

#### cURL

```bash
# Run workflow
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "workflow_001", "file_path": "workflows/sample_workflow.json"}'

# Get logs
curl http://localhost:8000/api/executions/abc123/logs
```

#### Node.js (fetch)

```javascript
async function runWorkflow() {
    const response = await fetch('http://localhost:8000/api/workflows/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workflow_id: 'workflow_001',
            file_path: 'workflows/sample_workflow.json'
        })
    });
    
    const result = await response.json();
    console.log(result);
}
```

---

## Skenario: Browser Sudah Login

### 📝 Update Data Berulang dari Excel/CSV

Jika Anda sudah login di browser dan ingin melakukan update data secara berulang:

#### 1. Persiapan Data Excel/CSV

Buat file `data/update_data.xlsx` dengan kolom yang sesuai:

| id | nama | email | status |
|----|------|-------|--------|
| 1  | John Doe | john@example.com | Aktif |
| 2  | Jane Smith | jane@example.com | Tidak Aktif |

#### 2. Workflow Example

Kami sudah menyediakan contoh workflow: `workflows/update_data_workflow_example.json`

Atau buat workflow baru dengan struktur:

```json
{
  "name": "Update Data (Browser Sudah Login)",
  "data_source": {
    "type": "excel",
    "config": {
      "file_path": "data/update_data.xlsx",
      "sheet": "Sheet1"
    }
  },
  "steps": [
    {
      "type": "wait",
      "label": "Wait browser siap",
      "params": {
        "wait_type": "until_visible",
        "selector": "body",
        "timeout": 10000
      }
    },
    {
      "type": "loop",
      "label": "Loop setiap baris data",
      "params": {
        "loop_type": "data_source",
        "data_source": "customers"
      }
    },
    {
      "type": "click",
      "label": "Klik tombol Edit",
      "params": {
        "selector": "#edit-{{data.id}}",
        "wait_before": 1000
      }
    },
    {
      "type": "input_text",
      "label": "Update nama",
      "params": {
        "selector": "#input-name",
        "value": "{{data.nama}}",
        "clear_first": true
      }
    },
    {
      "type": "click",
      "label": "Klik Save",
      "params": {
        "selector": "#btn-save",
        "wait_before": 500
      }
    }
  ]
}
```

#### 3. Langkah-langkah Penggunaan

1. **Login Manual**: Buka browser, login ke aplikasi, pastikan session aktif
2. **Jalankan Workflow**: Klik **Start** di Automation Studio
3. **Workflow otomatis**:
   - Wait browser siap
   - Loop sebanyak jumlah data di Excel
   - Untuk setiap baris: klik edit, isi form, save
   - Lanjut ke data berikutnya

#### 4. Variable Substitution

Gunakan `{{data.nama_kolom}}` untuk akses data Excel/CSV:

```json
{
  "value": "{{data.nama}}"
}
```

#### 5. Error Handling untuk Loop

Disarankan pakai `on_error: "continue"` agar jika satu baris gagal, lanjut ke berikutnya:

```json
{
  "type": "loop",
  "params": {
    "loop_type": "data_source",
    "data_source": "customers"
  },
  "on_error": "continue",
  "retry": {
    "max_retries": 2,
    "delay": 2000
  }
}
```

#### 6. Tips Penting

- **Headless Mode**: Set `headless: false` di `config.yaml` agar Anda bisa lihat browser
- **Wait Before**: Tambah `wait_before` untuk give time antar action
- **Screenshot on Error**: Enable `screenshot_on_error: true` untuk debugging
- **Data Validation**: Pastikan data Excel sudah benar sebelum run workflow

---

## FAQ & Tips

### 🔍 Frequently Asked Questions

**Q: Apakah Automation Studio gratis?**  
A: Ya, ini open-source project yang bisa digunakan dan dimodifikasi secara gratis.

**Q: Apakah bisa otomatis aplikasi desktop?**  
A: Bisa, gunakan action **Click** dengan `selector_type: "text"` atau fitur **Image Detection** untuk deteksi elemen visual.

**Q: Berapa maksimal step dalam satu workflow?**  
A: Tidak ada batasan teknis, tapi disarankan < 100 steps untuk performa optimal.

**Q: Apakah data saya aman?**  
A: Ya, semua data disimpan lokal di komputer Anda. Tidak ada data yang dikirim ke server eksternal (kecuali jika Anda menggunakan API data source).

**Q: Bisakah saya menambah action sendiri?**  
A: Ya, lihat dokumentasi developer di `PROJECT_PLAN.md` untuk membuat custom action.

### 💡 Tips & Tricks

#### 1. Gunakan CSS Selectors yang Efisien
```json
// ❌ Bad - terlalu spesifik
{
  "selector": "body > div > div > div > div > form > div:nth-child(3) > input"
}

// ✅ Good - gunakan ID atau class
{
  "selector": "#username"
}
```

#### 2. Tambahkan Wait untuk Siklus Loading
```json
{
  "type": "wait",
  "params": {
    "wait_type": "until_visible",
    "selector": ".loading-spinner",
    "timeout": 10000
  }
}
```

#### 3. Gunakan Variable Substitution
```json
{
  "value": "{{data.nama}} {{data.email}}"
}
```

#### 4. Handle Error dengan Skip
```json
{
  "on_error": "skip",  // Lanjut ke step berikutnya
  "retry": {
    "max_retries": 3,
    "delay": 2000
  }
}
```

#### 5. Debug dengan Screenshot
```json
{
  "monitoring": {
    "screenshot_on_error": true,
    "screenshot_on_step": true,
    "log_level": "DEBUG"
  }
}
```

#### 6. Gunakan If Else untuk Conditional Logic
```json
{
  "type": "if_else",
  "condition": {
    "variable": "{{data.status}}",
    "operator": "equals",
    "value": "Aktif"
  },
  "then": [
    {
      "type": "click",
      "params": { "selector": "#btn-activate" }
    }
  ],
  "else": [
    {
      "type": "click",
      "params": { "selector": "#btn-deactivate" }
    }
  ]
}
```

---

## Support & Kontribusi

- **Issues:** Buat issue di repository
- **Dokumentasi:** Lihat `PROJECT_PLAN.md` untuk arsitektur teknis
- **Kontribusi:** Fork, branch, dan Pull Request

---

## Changelog

### v1.0.0 (Juli 2026)
- ✅ Initial release
- ✅ 10+ actions (Click, Input Text, Select Dropdown, Upload File, Wait, Loop, If Else, HTTP Submit, Radio Select, Parallel Group)
- ✅ Browser Detection (CDP) for session reuse
- ✅ 4 data sources (Excel, CSV, Database, API)
- ✅ Desktop GUI dengan PySide6
- ✅ REST API dengan FastAPI
- ✅ Monitoring & Detection (OCR, Image)
- ✅ Build scripts untuk executable

---

**Selamat menggunakan Automation Studio! 🚀**