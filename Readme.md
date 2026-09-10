# 3D Shape Sandbox — Hand Gesture (Browser-only)

Versi ini **tidak lagi butuh Python/backend sama sekali**. Semua deteksi
tangan (MediaPipe Hands) dan render 3D (Three.js) jalan langsung di
browser — lebih ringan disetup, dan tracking-nya lebih "nempel" karena
tidak ada lagi delay kirim data lewat WebSocket + JPEG seperti versi lama.

`hand_tracker.py` dan `requirements.txt` sudah tidak diperlukan lagi
untuk versi ini (boleh dihapus, atau dibiarkan saja sebagai arsip).

## Cara Menjalankan

Karena browser butuh mengakses webcam langsung, jalankan lewat server
lokal (bukan langsung double-click file, supaya izin kamera pasti jalan):

```bash
cd folder-proyek-ini
python -m http.server 8000
```

Lalu buka `http://localhost:8000/index.html` di Chrome/Edge, dan klik
**Allow** saat browser minta izin kamera.

(Kalau kamu double-click `index.html` langsung dan ternyata browsermu
tetap mengizinkan kamera dari `file://`, itu juga boleh — tapi kalau
macet di layar loading, pindah ke cara server lokal di atas.)

## Cara Berinteraksi

| Gesture | Efek |
|---|---|
| ✌️👇 Angkat telunjuk+tengah, lalu turunkan keduanya **bersamaan** | Ganti jenis bentuk berikutnya (bola → kubus → kerucut → piramida → tabung → donat → ulang) |
| 💍👆 Dari posisi telunjuk+tengah tegak, ayunkan **jari manis ke atas** | Memunculkan 1 bentuk baru. Ayun turun lalu naik lagi untuk memunculkan 1 lagi, dan seterusnya — tidak akan spam walau tangan diam |
| 🤏 Pinch (jempol + telunjuk) di atas sebuah bentuk | Ambil & geser bentuk, mengikuti jari secara halus |
| 🤏🤏 Pegang bentuk dengan satu tangan, lalu pinch juga dengan tangan satunya di dekat bentuk itu | **Resize & rotate**: tarik tangan menjauh = besar, dekatkan = kecil, putar tangan = memutar bentuknya |
| ✌️ Bentuk gesture "V" (telunjuk + jari tengah, lainnya dilipat) | Ganti jenis bentuk berikutnya yang akan dibuat (bola → kubus → kerucut → piramida → tabung → donat → ulang) — muncul label mengambang menunjukkan pilihan saat ini |
| Lepas pinch di atas ikon 🗑️ (pojok kanan-bawah) | Menghapus bentuk yang sedang dipegang |
| Tekan `C` di keyboard | Bersihkan semua bentuk (opsional) |

Catatan: pinch sekarang murni untuk mengambil/menggeser/resize — tidak lagi
dipakai untuk membuat bentuk baru.

Dua tangan bisa dipakai bersamaan dan independen satu sama lain.

## Kalau Ada Masalah

- **Loading tidak selesai-selesai** — biasanya karena diakses lewat
  `file://` dan browser memblokir kamera. Jalankan lewat
  `python -m http.server 8000` seperti di atas.
- **"Kamera tidak bisa diakses"** — tutup aplikasi/tab lain yang mungkin
  memakai webcam (Zoom, Teams, tab video call lain), lalu refresh halaman.
- **Tracking terasa berat/patah-patah** — turunkan `modelComplexity` dari
  `1` ke `0` di bagian `hands.setOptions({...})` pada `index.html`, atau
  turunkan resolusi `width`/`height` di konfigurasi `Camera`.
- Mau atur seberapa sensitif pinch, radius ambil bentuk, kecepatan resize,
  dll — semua konstanta ada di bagian atas `<script>` pada `index.html`.

## Struktur Berkas

```
hand_gesture_3d/
├── index.html           # satu-satunya file yang perlu dijalankan
├── hand_tracker.py       # (arsip, tidak dipakai lagi di versi ini)
├── requirements.txt      # (arsip, tidak dipakai lagi di versi ini)
└── README.md
```