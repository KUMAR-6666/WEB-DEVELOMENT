# Crypto Market Simulation Backend - Phase 3

Backend API canggih untuk market kripto simulasi menggunakan Flask (Standar Industri).

## Fitur Baru (Phase 3)
1. **Pembatalan Pesanan (Cancel Order)**: User dapat membatalkan Limit Order yang pending dan saldo/koin akan dikembalikan.
2. **Statistik Pasar 24 Jam**: Setiap koin kini memiliki data High, Low, dan % Change dalam 24 jam terakhir.
3. **Paginasi (Pagination)**: Riwayat transaksi dan riwayat harga kini mendukung paginasi (`page` & `per_page`).
4. **JWT Refresh Token**: Sistem keamanan lebih baik dengan pemisahan Access Token dan Refresh Token.
5. **Validasi Input**: Pengecekan format email dan kekuatan password saat registrasi.

## Fitur Utama
- **Autentikasi JWT**: Registrasi, Login, dan Refresh Token.
- **Trading**: Market Order & Limit Order (dengan sistem locking aset).
- **Portfolio & Leaderboard**: Pantau aset dan peringkat pengguna berdasarkan total kekayaan.
- **Simulasi Harga**: Volatilitas dinamis berbasis waktu (Random Walk).
- **Market Wallet**: Pengumpulan fee trading (0.1%) ke dompet pengelola.
- **Dokumentasi Swagger**: API terdokumentasi lengkap di `/apidocs/`.

## Teknologi
- Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Cors, Flasgger, email-validator.

## Cara Menjalankan Secara Lokal
1. Install dependencies: `pip install -r requirements.txt`
2. Inisialisasi database: `python init_db.py`
3. Jalankan aplikasi: `python run.py`
4. Dokumentasi API: `http://localhost:5000/apidocs/`

## Endpoint API Utama
- `POST /api/auth/refresh`: Mendapatkan access token baru menggunakan refresh token.
- `POST /api/trade/limit-order/<id>/cancel`: Membatalkan pesanan pending.
- `GET /api/user/transactions?page=1&per_page=10`: Riwayat transaksi terpaginasi.
