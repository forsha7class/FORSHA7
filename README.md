# FORSHA 7

Halaman identitas kelas FORSHA 7, Bali Crystal College. Satu halaman statis:
`index.html`, plus foto di `img/`. Tanpa framework, tanpa bundler, tanpa npm,
tanpa langkah build.

## Menjalankan lokal

```
python3 -m http.server 8000
```

Buka <http://localhost:8000>. Membuka `index.html` langsung sebagai `file://`
juga jalan, tapi server lokal lebih akurat (beberapa browser membatasi hal-hal
kecil pada `file://`).

## Isi halaman

Seluruh daftar orang ada di `index.html`, di dalam array `PEOPLE`. Satu baris per
orang, satu sumber kebenaran. Halaman merender daftar, galeri, dan lightbox dari
array itu; tidak ada daftar kedua di HTML.

```js
{"n":1,"nama":"I Made Sukra Mahardika","role":"Korti","foto":"01"}
```

- `n` nomor urut, dipakai sebagai identitas di seluruh halaman
- `nama`, `role` teks apa adanya, otomatis di-escape
- `foto` kode berkas dua digit, atau `null` bila fotonya belum ada; baris tanpa
  foto tetap tampil, dengan inisial nama di tempat foto

Mengubah nama atau peran cukup di sini. Tidak ada tempat lain yang perlu
disunting.

## Menambah atau mengganti foto

Taruh berkas sumber lalu jalankan satu skrip:

```
# 1. simpan foto sebagai img/<kode>.webp, 1125x1500, sisi foto yang sama
#    namanya <kode>a.webp, yang kedua <kode>b.webp  (mis. img/12a.webp)
python3 tools/thumbs.py
```

Skrip itu menulis ulang turunan `-t` (400w) dan `-m` (800w) untuk semua foto.
Turunan boleh dihapus kapan saja, sumbernya berkas penuh. Konvensi nama:

```
img/12a.webp      1125w  sumber
img/12a-m.webp     800w  turunan
img/12a-t.webp     400w  turunan
```

Untuk mengisi #12 dan #14 yang belum ada fotonya: tambahkan berkas di atas, lalu
isi `"foto":"12"` dan `"foto":"14"` di array `PEOPLE`. Tidak ada perubahan kode
lain yang diperlukan.

`img/og-cover.jpg` (1200x630) adalah gambar preview saat tautan dibagikan.
Ganti bila foto sampulnya berubah.

## Berkas lain

- `DESIGN.md` kontrak desain (dials, palet, aturan yang dilarang, lantai
  aksesibilitas). Baca ini sebelum mengubah tampilan.
- `PRD.md` daftar pekerjaan v2 beserta metriknya.
- `404.html` halaman yang disajikan GitHub Pages untuk alamat salah.
