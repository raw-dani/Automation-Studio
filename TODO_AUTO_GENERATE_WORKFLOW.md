# TODO: Auto-Generate Workflow dari Data Excel

## 🎯 Tujuan
Membuat sistem yang bisa menghasilkan workflow otomatis dari data Excel, agar user tidak perlu build workflow manual untuk input data berulang.

## 📋 Checklist Implementasi
- [x] Analisis kebutuhan: mapping kolom Excel -> action/step workflow
- [x] Desain struktur mapping Excel -> workflow JSON
- [x] Tambah UI trigger "Auto Generate Workflow" di `frontend/ui/data_source_manager.py`
- [x] Buat backend parser Excel -> workflow JSON (`backend/core/workflow_builder.py`)
- [x] Buat backend generator workflow dari template action
- [x] Integrasi dengan `action_registry` agar `step_type` valid
- [x] Test dengan Excel sample berisi kolom standar form input
- [x] Dokumentasi dan contoh penggunaan

## 🔄 Status
- [x] Draft proposal
- [ ] Review & approval
- [ ] Implementasi
- [ ] Testing
- [ ] Deployment

## 📝 Catatan
- Fitur ini akan mempercepat pembuatan workflow untuk form input yang berulang
- Prioritas: Tinggi
- Estimasi: 2 minggu
