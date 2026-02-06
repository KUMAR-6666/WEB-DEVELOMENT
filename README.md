# Crypto Market Simulation Backend - Phase 2

Backend API canggih untuk market kripto simulasi menggunakan Flask.

## Fitur Baru (Phase 2)
1. **Riwayat Harga (Price History)**: Grafik harga koin kini bisa didukung dengan data history.
2. **Leaderboard**: Lihat peringkat kekayaan pengguna (Saldo + Aset).
3. **Limit Order**: Pasang beli/jual di harga target. Aset akan dikunci (locked) saat pesanan dipasang.
4. **Trading Fees & Market Wallet**: Fee 0.1% tiap transaksi yang dikumpulkan ke dompet pengelola (Market Wallet).
5. **Volatilitas Otomatis**: Harga berubah secara dinamis berdasarkan waktu (Random Walk) dan aktivitas pasar.
6. **Dokumentasi Swagger**: API terdokumentasi lengkap di `/apidocs/`.

## Fitur Utama
- **Autentikasi JWT**: Registrasi dan Login pengguna.
- **Trading**: Beli dan jual koin secara instan (Market Order) atau terjadwal (Limit Order).
- **Portfolio**: Pantau saldo koin dan nilai aset saat ini.
- **Deposit**: Tambah saldo virtual untuk pengujian.

## Struktur Proyek
```
app/
  models/      # Database models (User, Coin, Portfolio, Transaction, PriceHistory, LimitOrder)
  routes/      # API endpoints (auth, market, trade, user)
  services/    # Business logic (price_service, trade_service)
config.py      # Konfigurasi aplikasi
run.py         # Entry point aplikasi
init_db.py     # Skrip inisialisasi database
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
4. Buka Dokumentasi API:
   `http://localhost:5000/apidocs/`

## Panduan Deployment di PythonAnywhere
(Sama seperti sebelumnya, pastikan menjalankan `python init_db.py` untuk skema database baru).

## Endpoint API Utama
- `GET /apidocs/`: Dokumentasi Lengkap
- `GET /api/user/leaderboard`: Peringkat kekayaan
- `GET /api/market/<symbol>/history`: Data grafik harga
- `POST /api/trade/limit-order`: Memasang Limit Order
