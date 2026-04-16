# 📊 Networth Portfolio Tracker — Streamlit

Tracker portfolio bulanan dengan fitur yield/passive income.

## 🚀 Cara Deploy ke Streamlit Cloud (Gratis, Akses via Chrome)

### **Langkah 1: Upload ke GitHub**

1. Buat akun GitHub di https://github.com (kalau belum punya)
2. Buat repository baru → klik **New repository**
   - Nama: `portfolio-tracker` (atau terserah)
   - Set **Public** (Streamlit Cloud gratis hanya untuk repo public)
   - Klik **Create repository**
3. Upload 3 file ini ke repository tersebut:
   - `app.py`
   - `requirements.txt`
   - `README.md`

   **Cara termudah:** klik tombol **Add file → Upload files**, drag-drop semua file, lalu klik **Commit changes**.

### **Langkah 2: Deploy di Streamlit Cloud**

1. Buka https://share.streamlit.io
2. Klik **Sign in** → login pakai akun GitHub
3. Klik tombol **Create app** → pilih **Deploy a public app from GitHub**
4. Isi form:
   - **Repository:** pilih repo `portfolio-tracker` yang tadi dibuat
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** bebas, misalnya `andreas-portfolio` (URL jadi `https://andreas-portfolio.streamlit.app`)
5. Klik **Deploy**

Tunggu 1-2 menit. Setelah selesai, app-nya bisa langsung diakses via URL tersebut dari Chrome (atau browser apapun, di HP maupun laptop).

---

## 💻 Atau Jalankan Lokal (Opsi Alternatif)

Kalau mau coba dulu di laptop sendiri:

```bash
# Install Python 3.9+ dulu kalau belum ada
pip install -r requirements.txt
streamlit run app.py
```

Akan kebuka otomatis di browser di `http://localhost:8501`.

---

## ⚠️ Catatan Penting Soal Data

Streamlit Cloud **menyimpan data di file `portfolio_data.json`** yang ada di server. Tapi:

- **Data bisa hilang** kalau app di-restart atau redeploy oleh Streamlit Cloud (sifatnya ephemeral storage).
- **Solusi:** pakai fitur **💾 Backup/Restore** di sidebar:
  - **Download JSON** setelah input data → simpan di laptop/Google Drive
  - **Upload JSON** kalau data hilang atau mau pindah device

Kalau butuh storage permanen, bisa upgrade ke solusi seperti:
- Google Sheets integration (pakai `gspread`)
- Supabase / Firebase (database gratis)
- AWS S3 untuk simpan JSON file

Saya bisa bantu setup itu juga kalau butuh.

---

## 🎯 Fitur

- **Dashboard:** net worth, perubahan bulanan, passive income, CAGR, charts lengkap
- **Input:** nilai aset + yield per kategori, dengan deskripsi/catatan
- **Riwayat:** semua data bulanan, bisa edit/hapus, bisa expand lihat detail
- **Analisis:** bulan terbaik/terburuk, CAGR, trend passive income, skor diversifikasi
- **Export/Import:** backup data ke JSON, export ke CSV

### 8 Kategori Aset
Saham · Crypto · Deposito · Reksadana · Emas · Cash · Properti · Lainnya

Masing-masing punya label yield custom (Dividen, Staking, Bunga, Sewa, dll).
