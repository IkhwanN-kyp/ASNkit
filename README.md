# ASNkit

<img src="asnkit.svg" alt="ASNkit" width="96">

Toolkit PDF desktop berbahasa Indonesia, berbasis Python dan PySide6. Versi Linux 1.3.0.

## Fitur

- Gabungkan dan pisahkan PDF.
- Konversi PDF ke Word (DOCX), serta Word ke PDF melalui LibreOffice.
- **PDF ke Markdown (.md)** menggunakan [Microsoft MarkItDown](https://github.com/microsoft/markitdown).
- **Gambar ke Markdown (.md)** melalui converter OCR lokal Tesseract yang didaftarkan pada Microsoft MarkItDown; bahasa Indonesia dan Inggris.
- **Gemini → Markdown** opsional untuk transkripsi gambar dengan AI Google.
- Gabungkan gambar menjadi PDF.
- PDF viewer dengan navigasi halaman dan zoom.
- Tema gelap/terang dan ikon khusus ASNkit.

Alat PDF dan OCR Tesseract diproses lokal tanpa API key. Tab Gemini bersifat opsional dan mengirim gambar ke Google dengan API key serta persetujuan pengguna. PDF hasil scan membutuhkan OCR terlebih dahulu; tata letak kompleks dan tabel dapat berubah saat konversi.

## Instalasi Linux

Diuji menggunakan Python 3.14.4. Paket Python di requirements.txt dipatok sesuai lingkungan yang diuji.

Pada Debian/Ubuntu, siapkan Python, venv, dan LibreOffice:

```bash
sudo apt install python3 python3-venv libreoffice tesseract-ocr tesseract-ocr-ind tesseract-ocr-eng
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

## Gambar ke Markdown

1. Buka tab **Gambar → MD**.
2. Tambahkan satu PNG, JPEG, BMP, TIFF, atau WebP.
3. Pilih bahasa Indonesia, Inggris, atau keduanya.
4. Untuk foto buku, klik **Pilih area baca…**. Seret beberapa kotak sesuai urutan baca, misalnya judul, teks kolom kiri, lalu kolom kanan. Hindari ilustrasi serta halaman sebelah. Gambar asli tidak diubah.
5. Pilih susunan **Satu blok teks per area** untuk potongan paragraf; atau **Dua kolom** untuk area yang mencakup dua kolom. Sesuaikan persentase batas kolom jika pembatas tidak berada tepat di tengah. Dalam mode dua kolom, setiap area dibaca dari kolom kiri lalu kanan.
6. Klik **Simpan gambar sebagai Markdown**.

Pilihan area berlaku untuk gambar tersebut saja dan dibersihkan ketika sumber berubah. Foto melengkung, miring, buram, atau teks tertutup tetap dapat salah terbaca; pemilihan area tidak meluruskan perspektif atau memulihkan teks yang hilang.

ASNkit mendaftarkan converter gambar khusus pada MarkItDown yang memakai Tesseract lokal. Ini merupakan integrasi ASNkit, bukan OCR lokal bawaan MarkItDown. Tidak membutuhkan API key atau unggahan gambar. Gambar diputar mengikuti orientasi EXIF; TIFF multihalaman diproses per halaman. Hasil berupa teks OCR dalam file Markdown, bukan rekonstruksi tabel, format, atau deskripsi visual. Periksa kembali hasil OCR; tulisan tangan dan gambar buram dapat kurang akurat. Gambar tanpa teks menghasilkan pesan kesalahan tanpa mengganti file hasil sebelumnya.

Pasang paket Tesseract beserta bahasa yang dipilih menggunakan perintah instalasi di atas. Instalasi lokal khusus komputer asal tidak disertakan dalam repositori.

## Gemini ke Markdown (opsional, daring)

1. Buka [Google AI Studio](https://aistudio.google.com/apikey), login Google, dan buat Gemini API key. Integrasi desktop ini memakai API key, bukan sesi login Gemini di browser.
2. Buka tab **Gemini → MD** di ASNkit dan tambahkan tepat satu gambar.
3. Tempel API key. Key hanya disimpan dalam memori selama sesi aplikasi; tidak ditulis ke file atau argumen proses.
4. Pilih model yang tersedia untuk proyek Anda. Default: `gemini-3.5-flash-lite`; ID model dapat diedit.
5. Baca informasi pengiriman data, lalu centang persetujuan gambar dikirim ke Google.
6. Klik **Kirim ke Gemini dan simpan Markdown**, lalu pilih lokasi hasil.

Gemini mempunyai free tier untuk model/proyek tertentu, dengan kuota dan pembatasan. Pengguna harus memeriksa [harga/ketentuan data Google](https://ai.google.dev/gemini-api/docs/pricing) dan kuota proyeknya; aplikasi tidak dapat menjamin penggunaan gratis pada proyek berbayar. Pada layanan gratis, konten dapat dipakai Google untuk meningkatkan produknya. Jangan menaruh API key dalam kode atau repositori.

Mode ini mengirim gambar dari tab Gemini saja. Mode OCR lokal serta pilihan areanya terpisah dan tidak memakai Gemini. Gambar diputar sesuai EXIF, metadata dibuang, dan resolusi dibatasi maksimum 3072 piksel per sisi sebelum dikirim. TIFF didukung hingga 10 halaman per permintaan, dengan batas payload aplikasi 19 MB. Foto asli tidak diubah. Persetujuan pengiriman direset setelah permintaan dijalankan atau daftar gambar berubah.

Prompt meminta transkripsi sesuai urutan kolom tanpa menjawab soal; teks tidak jelas ditandai `[tidak terbaca]` dan ilustrasi ditandai `[Ilustrasi]`. Hasil AI tetap dapat salah dan harus diperiksa. Respons kosong, terblokir, terpotong, atau HTTP error tidak mengganti file hasil sebelumnya. Aplikasi tidak mencoba ulang permintaan secara otomatis.

Integrasi telah diuji dengan respons API simulasi. Pengujian langsung ke Google memerlukan API key pengguna; tidak ada key yang disertakan.

## Asal dan lisensi

Diadaptasi dari kode sumber ASNkit versi Windows 1.0.1 yang disertakan dalam ASNkit.zip. Adaptasi Linux mencakup konversi Word melalui LibreOffice, ikon khusus, serta integrasi Microsoft MarkItDown.

Kode ASNkit menggunakan [MIT License](LICENSE.txt); atribusi asli dipertahankan. Dependensi tetap mengikuti lisensi masing-masing. Dukungan untuk pengembang asli: [Trakteer @radarswingid](https://trakteer.id/radarswingid).
