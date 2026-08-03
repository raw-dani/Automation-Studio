# 📦 Daftar Modul Utama — Automation Studio

Dokumen ini berisi daftar lengkap modul utama aplikasi **Automation Studio**, beserta fungsi dan file pentingnya.

---

## 1. 🎯 Modul Core (Backend Inti)

Lokasi: `backend/core/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Workflow Parser** | `workflow_parser.py` | Parsing, validasi, dan serialisasi file workflow JSON. Membuat objek `Workflow` dan `WorkflowStep`. |
| **Action Registry** | `action_registry.py` | Mendaftarkan dan mengelola semua action (pola Registry). Memudahkan penambahan action baru. |
| **Execution Engine** | `engine.py` | Mesin utama pengeksekusi workflow menggunakan Playwright. Mendukung retry, pause, resume, stop, screenshot, progress tracking, data source loop, dan parallel group. |

---

## 2. 🖱️ Modul Actions (Aksi Otomasi)

Lokasi: `backend/actions/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Base Action** | `base_action.py` | Kelas abstrak dasar untuk semua action. Berisi `ExecutionContext`, `ActionResult`, dan `ActionStatus`. |
| **Click** | `click_action.py` | Aksi klik pada elemen web. |
| **Input Text** | `input_text_action.py` | Aksi mengisi nilai pada input teks. |
| **Input Date** | `input_date_action.py` | Aksi mengisi tanggal pada input date. |
| **Wait** | `wait_action.py` | Aksi menunggu elemen muncul / delay. |
| **Navigate** | `navigate_action.py` | Aksi navigasi / berpindah halaman (goto URL). |
| **Select Dropdown** | `select_dropdown_action.py` | Aksi memilih opsi pada `<select>` dropdown. |
| **Select (Custom)** | `select_action.py` | Aksi memilih opsi pada dropdown custom. |
| **Select2** | `select2_action.py` | Aksi memilih opsi pada dropdown Select2. |
| **Radio Select** | `radio_select_action.py` | Aksi memilih opsi pada radio button. |
| **Upload File** | `upload_file_action.py` | Aksi upload file melalui input file. |
| **HTTP Submit** | `http_submit_action.py` | Aksi submit HTTP request (POST/GET). |
| **Loop** | `loop_action.py` | Aksi perulangan (loop data source / fixed count). |
| **If Else** | `if_else_action.py` | Aksi percabangan kondisi. |
| **Parallel Group** | `parallel_group_action.py` | Aksi menjalankan beberapa step secara concurrent/paralel. |

---

## 3. 📊 Modul Data Sources (Sumber Data)

Lokasi: `backend/data_sources/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Base Source** | `base_source.py` | Kelas abstrak dasar untuk semua data source. Berisi `DataRow`. |
| **Excel** | `excel_source.py` | Membaca data dari file Excel (`.xlsx` / `.xls`). |
| **CSV** | `csv_source.py` | Membaca data dari file CSV. |
| **Database** | `database_source.py` | Membaca data dari database (SQLAlchemy). |
| **API** | `api_source.py` | Membaca data dari REST API. |

---

## 4. 📈 Modul Monitoring

Lokasi: `backend/monitoring/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Logger** | `logger.py` | Pencatatan log eksekusi. |
| **Screenshot** | `screenshot.py` | Pengambilan screenshot saat step berhasil / error. |
| **Progress Tracker** | `progress_tracker.py` | Pelacakan progress eksekusi workflow. |
| **Resume Handler** | `resume_handler.py` | Mendukung resume eksekusi dari step tertentu Jika gagal. |

---

## 5. 🔍 Modul Detectors (Deteksi)

Lokasi: `backend/detectors/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Base Detector** | `base_detector.py` | Kelas abstrak dasar untuk semua detector. |
| **OCR Detector** | `ocr_detector.py` | Deteksi teks dari gambar menggunakan OCR (pytesseract). |
| **Image Detector** | `image_detector.py` | Deteksi elemen berdasarkan pencocokan gambar (OpenCV). |

---

## 6. 🌐 Modul API (Opsional)

Lokasi: `backend/api/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Routes** | `routes.py` | Definisi endpoint REST API (FastAPI). |
| **Schemas** | `schemas.py` | Model Pydantic untuk request/response API. |

---

## 7. 🖥️ Modul Frontend UI (Desktop)

Lokasi: `frontend/ui/`

| Modul | File | Fungsi |
|-------|------|--------|
| **Main Window** | `main_window.py` | Jendela utama aplikasi. Menyusun layout splitter (Palette | Editor | Panel kanan), menu bar, toolbar, status bar, shortcut, dan recent files. |
| **Workflow Editor** | `workflow_editor.py` | Editor workflow berbasis tree view. Mendukung nested children (loop, parallel group, if_else), undo/redo, move up/down, dan duplicate node. |
| **Action Palette** | `action_palette.py` | Panel kiri berisi daftar action yang bisa ditambahkan ke workflow (drag / klik). |
| **Properties Panel** | `properties_panel.py` | Panel untuk mengedit parameter step yang dipilih (selector, value, dll). |
| **Data Source Manager** | `data_source_manager.py` | Panel untuk mengonfigurasi data source workflow (Excel, CSV, API, Database). |
| **Execution Panel** | `execution_panel.py` | Panel untuk menjalankan workflow: Run, Pause/Resume, Stop, dan menampilkan hasil eksekusi. |
| **Monitoring Panel** | `monitoring_panel.py` | Panel untuk menampilkan log, progress, dan status eksekusi secara real-time. |

---

## 8. 🚀 Entry Points

| Modul | File | Fungsi |
|-------|------|--------|
| **CLI (Command Line)** | `main.py` | Entry point CLI: `run`, `list`, `validate`, `actions`, `preview-excel`, `preview-csv`. |
| **Desktop (GUI)** | `frontend/main.py` | Entry point aplikasi desktop PySide6. |
| **Build Script** | `build_exe.py` | Script pembuatan executable (EXE). |

---

## 9. ⚙️ Konfigurasi & Data

| Modul | Lokasi | Fungsi |
|-------|--------|--------|
| **Config Global** | `config.yaml` | Konfigurasi global: Playwright browser, session mode, performance mode, paths, monitoring, dll. |
| **Workflows** | `workflows/` | Penyimpanan file workflow JSON (contoh: `MelengkapiBidangTanah.json`, `isi_data_pelanggan.json`, dll). |
| **Data Files** | `data/` | Contoh file data source (Excel/CSV) untuk otomasi. |
| **Screenshots** | `screenshots/` | Folder penyimpanan screenshot hasil eksekusi. |

---

## 10. 📋 Ringkasan Modul per Layer

```
┌─────────────────────────────────────────────────┐
│                 ENTRY POINTS                    │
│   main.py (CLI)  •  frontend/main.py (GUI)      │
├─────────────────────────────────────────────────┤
│                 FRONTEND (UI)                   │
│   MainWindow  →  Editor  →  Palette             │
│      ↓            ↓          ↓                  │
│   Properties  •  DataSource  •  Execution       │
│      ↓            ↓          ↓                  │
│              Monitoring Panel                   │
├─────────────────────────────────────────────────┤
│                 BACKEND (Core)                  │
│   Execution Engine  →  Action Registry          │
│                ↓                                │
│           Workflow Parser                       │
├─────────────────────────────────────────────────┤
│              COMPONENTS                         │
│   Actions  •  Data Sources  •  Monitoring       │
│   Detectors  •  API (FastAPI)                   │
├─────────────────────────────────────────────────┤
│              KONFIGURASI & DATA                 │
│   config.yaml  •  workflows/  •  data/          │
└─────────────────────────────────────────────────┘
```

---

## 📝 Catatan

- **Modul Actions** saat ini berisi **14 action konkret** + 1 base class.
- **Modul Data Sources** berisi **4 data source** + 1 base class.
- **Frontend** menggunakan framework **PySide6 (Qt for Python)**.
- **Backend** menggunakan **Playwright** untuk otomasi browser.
- Modul dapat dikembangkan lebih lanjut dengan menambahkan action baru, data source baru, dan detector baru tanpa mengubah modul inti.