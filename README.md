# ASNkit

<img src="asnkit.svg" alt="ASNkit" width="96">

Toolkit PDF desktop berbahasa Indonesia, berbasis Python dan PySide6. Versi Linux 1.1.0.

## Fitur

- Gabungkan dan pisahkan PDF.
- Konversi PDF ke Word (DOCX), serta Word ke PDF melalui LibreOffice.
- **PDF ke Markdown (.md)** menggunakan [Microsoft MarkItDown](https://github.com/microsoft/markitdown).
- Gabungkan gambar menjadi PDF.
- PDF viewer dengan navigasi halaman dan zoom.
- Tema gelap/terang dan ikon khusus ASNkit.

Dokumen diproses secara lokal. Konversi Markdown tidak membutuhkan API key atau layanan AI daring. PDF hasil scan membutuhkan OCR terlebih dahulu; tata letak kompleks dan tabel dapat berubah saat konversi.

## Instalasi Linux

Diuji menggunakan Python 3.14.4. Paket Python di requirements.txt dipatok sesuai lingkungan yang diuji.

Pada Debian/Ubuntu, siapkan Python, venv, dan LibreOffice:

```bash
sudo apt install python3 python3-venv libreoffice
```

Unduh atau clone repositori ini, kemudian dari folder proyek jalankan:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
sh launch.sh
```

Jika `ensurepip` tidak tersedia, pasang paket venv yang sesuai versi Python distribusi Anda, atau gunakan pip sistem untuk mengisi venv:

```bash
python3 -m pip --python venv/bin/python install -r requirements.txt
```

## Shortcut

Dari folder proyek:

```bash
venv/bin/python install-shortcut.py
```

Shortcut dibuat di menu aplikasi dan Desktop. Jika desktop meminta izin peluncuran, pilih **Allow Launching / Izinkan Peluncuran**. Jangan pindahkan folder proyek setelah memasang shortcut; jalankan ulang pemasang shortcut jika lokasi berubah.

## PDF ke Markdown

1. Buka tab **PDF → Markdown**.
2. Tambahkan tepat satu PDF.
3. Klik **Simpan sebagai Markdown**, lalu pilih lokasi file `.md`.

Konversi berjalan dalam proses terpisah agar jendela tetap responsif. Jika konversi gagal atau PDF tidak mengandung teks, file hasil yang sudah ada tidak diganti.

## Asal dan lisensi

Diadaptasi dari kode sumber ASNkit versi Windows 1.0.1 yang disertakan dalam ASNkit.zip. Adaptasi Linux mencakup konversi Word melalui LibreOffice, ikon khusus, serta integrasi Microsoft MarkItDown.

Kode ASNkit menggunakan [MIT License](LICENSE.txt); atribusi asli dipertahankan. Dependensi tetap mengikuti lisensi masing-masing. Dukungan untuk pengembang asli: [Trakteer @radarswingid](https://trakteer.id/radarswingid).
