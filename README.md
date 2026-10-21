# FORSHA 7

Halaman identitas kelas FORSHA 7, Bali Crystal College. Satu halaman statis:
`index.html`, plus foto di `img/`, GSAP dan font Outfit di `vendor/`. Tanpa
framework, tanpa bundler, tanpa langkah build, tanpa permintaan ke pihak ketiga.

## Menjalankan lokal

```
python3 -m http.server 8000
```

Buka <http://localhost:8000>. Jangan pakai `file://`: GSAP dan beberapa browser
membatasi pemuatan berkas lokal.

## Isi halaman

Seluruh daftar orang ada di `index.html`, di dalam array `PEOPLE`. Satu baris per
orang, satu sumber kebenaran. Dinding kelas, galeri, pencarian, profil, dan
formasi penutup semuanya dirender dari array itu.

```js
{"n":1,"nama":"I Made Sukra Mahardika","role":"Korti","foto":"01"}
```

- `n` nomor urut, dipakai sebagai identitas di seluruh halaman
- `nama`, `role` teks apa adanya, otomatis di-escape
- `foto` kode berkas dua digit, atau `null` bila fotonya belum ada; baris tanpa
  foto tetap tampil, dengan inisial nama di tempat foto

Mengubah nama atau peran cukup di sini.

## Struktur halaman

- **Hero / The Corridor** — koridor potret, class pass, judul, CTA.
- **The Wall** — 20 kartu, filter Everyone / Committee / Members, hover flip,
  klik membuka profil. Pencarian nama lewat tombol "Find your name" atau `/`.
- **Disciplines** — Front Office dan Housekeeping.
- **Plates** — dua baris marquee 36 foto, klik membuka lightbox.
- **About** — konteks kelas dan angka.
- **Close** — 20 kartu menyusun angka 7, lalu penutup.

## Menambah atau mengganti foto

Taruh berkas sumber lalu jalankan satu skrip:

```
# 1. simpan foto sebagai img/<kode>.webp, 1125x1500, sisi foto yang sama
#    namanya <kode>a.webp, yang kedua <kode>b.webp  (mis. img/12a.webp)
python3 tools/thumbs.py
```

Skrip itu menulis ulang turunan `-t` (400w) dan `-m` (800w) untuk semua foto.
Konvensi nama:

```
img/12a.webp      1125w  sumber
img/12a-m.webp     800w  turunan
img/12a-t.webp     400w  turunan
```

Untuk mengisi #12 dan #14 yang belum ada fotonya: tambahkan berkas di atas, lalu
isi `"foto":"12"` dan `"foto":"14"` di array `PEOPLE`. Tidak ada perubahan kode
lain yang diperlukan.

`img/og-cover.jpg` (1200x630) adalah gambar preview saat tautan dibagikan.

## Animasi

GSAP 3.13 (core + ScrollTrigger) dan font Outfit di-vendor di `vendor/`, tanpa
CDN, jadi halaman tetap jalan offline. `prefers-reduced-motion` menghapus semua
pergerakan (termasuk marquee) dan menampilkan versi statis yang lengkap.

Poles v3 menambahkan gerak masuk yang seluruhnya CSS, dipicu oleh kelas
`.overlay.open`: kartu profil mendarat dari blur, lightbox menampilkan salinan
potret yang diburamkan sebagai latar yang melayang pelan, dan pelat galeri
terangkat saat disentuh maupun difokus. Salinan blur itu memakai berkas foto
yang sama, jadi tidak menambah permintaan. `404.html` memakai gerak masuk yang
sama dan tetap tanpa JavaScript serta tanpa gambar.

Catatan penting: jangan menambahkan `scroll-behavior: smooth` di CSS. Itu
mengacaukan pengukuran ScrollTrigger. Smooth scroll untuk anchor sudah diatur
lewat JavaScript.

## Verifikasi

`tools/verify_motion.py` menguji klaim halaman di browser sungguhan: 81
pemeriksaan untuk gerak (GSAP/ScrollTrigger), gambar, aksesibilitas, formasi
penutup, reduced motion, overflow di 320/390/820/1440 px, dan poles v3 (profil
yang mendarat, latar lightbox yang melayang, hover pelat, serta halaman 404).
Skrip mencetak laporan `ok`/`FAIL` dan keluar dengan kode non-nol bila ada yang
gagal.

```
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tools/verify_motion.py
```

Skrip menjalankan server pratinjau sendiri yang threaded. Untuk pratinjau manual
pakai juga server threaded: `python3 -m http.server` melayani satu permintaan
sekaligus, dan halaman ini membuka puluhan gambar sekaligus saat first paint.

## Berkas lain

- `DESIGN.md` kontrak desain v3 (konsep, token, motion, aksesibilitas).
- `PRD.md` catatan pekerjaan v2; sebagian metrik visualnya sudah digantikan v3.
- `404.html` halaman yang disajikan GitHub Pages untuk alamat salah; berdiri
  sendiri, tanpa JavaScript dan tanpa gambar.
- `vendor/` GSAP, ScrollTrigger, dan font Outfit (self-hosted).
- `vendor/fonts/outfit.css` subset CSS dari Google Fonts (lisensi SIL OFL 1.1);
  dua berkas woff2 menutup lima bobot, latin dan latin-ext.
- `tools/` skrip bantu: `thumbs.py` (turunan gambar) dan `verify_motion.py`.
