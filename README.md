# Crypto Market Simulation Backend

Backend API untuk market kripto simulasi menggunakan Flask.

## Fitur
- **Autentikasi JWT**: Registrasi dan Login pengguna.
- **Simulasi Pasar**: Daftar 10 koin teratas dengan harga yang berubah berdasarkan permintaan pasar (beli/jual).
- **Trading**: Beli dan jual koin menggunakan saldo virtual.
- **Portfolio**: Pantau saldo koin dan nilai aset saat ini.
- **Deposit**: Tambah saldo virtual untuk pengujian.

## Teknologi
- Flask
- Flask-SQLAlchemy (SQLite)
- Flask-JWT-Extended
- Flask-CORS

## Struktur Proyek
```
app/
  models/      # Database models
  routes/      # API endpoints (Blueprints)
  services/    # Business logic (Price simulation)
config.py      # Konfigurasi aplikasi
run.py         # Entry point aplikasi
init_db.py     # Skrip inisialisasi database & koin
```

## Cara Menjalankan Secara Lokal
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Inisialisasi database:
   ```bash
   python init_db.py
   ```
3. Jalankan aplikasi:
   ```bash
   python run.py
   ```

## Panduan Deployment di PythonAnywhere

1. **Upload Kode**:
   - Zip folder proyek Anda atau gunakan Git untuk clone ke PythonAnywhere.
   - Buka bash console di PythonAnywhere.

2. **Setup Virtual Environment**:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 my-venv
   pip install -r requirements.txt
   ```

3. **Inisialisasi Database**:
   ```bash
   python init_db.py
   ```

4. **Konfigurasi Web Tab**:
   - Pergi ke tab **Web** di dashboard PythonAnywhere.
   - Klik **Add a new web app**.
   - Pilih **Manual Configuration** -> **Python 3.10**.
   - Atur **Virtualenv** path ke: `/home/USERNAME/.virtualenvs/my-venv`.
   - Atur **Source code** path ke: `/home/USERNAME/your-project-folder`.

5. **Edit WSGI File**:
   Klik pada link "WSGI configuration file" dan ubah isinya menjadi:
   ```python
   import sys
   import os

   path = '/home/USERNAME/your-project-folder'
   if path not in sys.path:
       sys.path.append(path)

   from run import app as application
   ```
   *(Ganti USERNAME dan your-project-folder sesuai dengan akun Anda)*

6. **Reload Web App**:
   Klik tombol **Reload** di tab Web.

## Endpoint API Utama
- `POST /api/auth/register`: Username, Email, Password
- `POST /api/auth/login`: Username, Password
- `GET /api/market/`: List semua koin
- `POST /api/user/deposit`: Amount (Butuh JWT)
- `POST /api/trade/buy`: Symbol, Amount (Butuh JWT)
- `POST /api/trade/sell`: Symbol, Amount (Butuh JWT)
- `GET /api/user/portfolio`: Cek aset (Butuh JWT)
