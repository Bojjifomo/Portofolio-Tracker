💻 Atau Jalankan Lokal (Opsi Alternatif)
Kalau mau coba dulu di laptop sendiri:
bash# Install Python 3.9+ dulu kalau belum ada
pip install -r requirements.txt
streamlit run app.py
Akan kebuka otomatis di browser di http://localhost:8501.

⚠️ Catatan Penting Soal Data
Streamlit Cloud menyimpan data di file portfolio_data.json yang ada di server. Tapi:

Data bisa hilang kalau app di-restart atau redeploy oleh Streamlit Cloud (sifatnya ephemeral storage).
Solusi: pakai fitur 💾 Backup/Restore di sidebar:

Download JSON setelah input data → simpan di laptop/Google Drive
Upload JSON kalau data hilang atau mau pindah device



Kalau butuh storage permanen, bisa upgrade ke solusi seperti:

Google Sheets integration (pakai gspread)
Supabase / Firebase (database gratis)
AWS S3 untuk simpan JSON file

Saya bisa bantu setup itu juga kalau butuh.

🎯 Fitur

Dashboard: net worth, perubahan bulanan, passive income, CAGR, charts lengkap
Input: nilai aset + yield per kategori, dengan deskripsi/catatan
Riwayat: semua data bulanan, bisa edit/hapus, bisa expand lihat detail
Analisis: bulan terbaik/terburuk, CAGR, trend passive income, skor diversifikasi
Export/Import: backup data ke JSON, export ke CSV

8 Kategori Aset
Saham · Crypto · Deposito · Reksadana · Emas · Cash · Properti · Lainnya
Masing-masing punya label yield custom (Dividen, Staking, Bunga, Sewa, dll).
