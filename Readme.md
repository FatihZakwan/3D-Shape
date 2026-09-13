# 3D Shape Sandbox — Hand Gesture (Browser-only, Offline)

Semua deteksi tangan (MediaPipe Hands) dan render 3D (Three.js) jalan
langsung di browser — tidak butuh Python/backend, dan setelah setup awal
**bisa jalan 100% offline** (library sudah dibundel lokal di folder
`vendor/`, tinggal model AI-nya yang perlu sekali download manual).

## Setup Awal (sekali saja)

1. Download file model AI di link ini (buka di browser, otomatis kedownload):
   ```
   https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
   ```
2. Pindahkan file hasil download itu ke folder `models/`, sehingga jadi:
   ```
   models/hand_landmarker.task
   ```
   (lihat `models/BACA_INI.txt` kalau lupa link-nya)

Setelah itu, kamu tidak perlu internet lagi untuk menjalankan aplikasi ini.

## Cara Menjalankan

```bash
cd folder-proyek-ini
python -m http.server 8666
```

Lalu buka `http://localhost:8666/index.html` di Chrome/Edge, dan klik
**Allow** saat browser minta izin kamera.

(Boleh pakai port lain kalau mau, `8666` cuma contoh — tidak ada bagian
kode yang bergantung ke nomor port tertentu.)

## Cara Berinteraksi

| Gesture | Efek |
|---|---|
| 👍 Tegakkan **jempol** | Memunculkan **Bola** |
| ☝️ Tegakkan **telunjuk** | Memunculkan **Kubus** |
| 🖕 Tegakkan **jari tengah** | Memunculkan **Kerucut** |
| 💍 Tegakkan **jari manis** | Memunculkan **Piramida** |
| 🤙 Tegakkan **kelingking** | Memunculkan **Tabung** |
| 🤏 Pinch (jempol + telunjuk) di atas sebuah bentuk | Ambil & geser bentuk, mengikuti jari secara halus |
| 🤏🤏 Pegang bentuk dengan satu tangan, lalu pinch juga dengan tangan satunya di dekat bentuk itu | **Resize & rotate**: tarik tangan menjauh = besar, dekatkan = kecil, putar tangan = memutar bentuknya |
| Lepas pinch di atas ikon 🗑️ (pojok kanan-bawah) | Menghapus bentuk yang sedang dipegang |
| Tekan `C` di keyboard | Bersihkan semua bentuk (opsional) |

Catatan penting:
- Tiap jari cuma memunculkan bentuk **sekali per tegak** (edge-triggered) —
  tegakkan jari, muncul 1 bentuk; turunkan lalu tegakkan lagi, muncul 1 lagi.
  Menahan jari tetap tegak tidak akan terus-menerus memunculkan bentuk baru.
- Pinch murni untuk mengambil/menggeser/resize — tidak dipakai untuk membuat
  bentuk baru sama sekali.
- Dua tangan bisa dipakai bersamaan dan independen satu sama lain.

## Kalau Ada Masalah

- **Loading tidak selesai-selesai** — biasanya karena diakses lewat
  `file://` dan browser memblokir kamera/module import. Jalankan lewat
  `python -m http.server 8666` seperti di atas.
- **"Model gagal dimuat"** — pastikan `models/hand_landmarker.task` sudah
  ada persis di path itu (lihat Setup Awal).
- **"Kamera tidak bisa diakses"** — tutup aplikasi/tab lain yang mungkin
  memakai webcam (Zoom, Teams, tab video call lain), lalu refresh halaman.
- **Tracking terasa berat/patah-patah** — turunkan resolusi di bagian
  `getUserMedia({ video: {...} })` pada `index.html`.
- Mau atur sensitivitas gesture (ambang pinch, radius ambil bentuk,
  kecepatan resize, margin deteksi jari) — semua konstanta ada di bagian
  atas `<script>` pada `index.html`.

## Struktur Berkas

```
hand_gesture_3d/
├── index.html                    # satu-satunya file yang perlu dijalankan
├── vendor/
│   ├── three.min.js               # Three.js (offline, dari npm)
│   └── mediapipe/
│       ├── vision_bundle.mjs      # MediaPipe Tasks Vision (offline, dari npm)
│       └── wasm/                  # runtime WASM MediaPipe (offline, dari npm)
├── models/
│   ├── hand_landmarker.task       # model AI (kamu download manual sekali)
│   └── BACA_INI.txt
├── hand_tracker.py                # (arsip, tidak dipakai lagi di versi ini)
├── requirements.txt               # (arsip, tidak dipakai lagi di versi ini)
└── README.md
```

Folder `vendor/` aman untuk ikut di-commit ke git (total ~19MB, semuanya
di bawah batas ukuran file GitHub). File `models/hand_landmarker.task`
(~7-8MB) juga aman di-commit setelah kamu download.
