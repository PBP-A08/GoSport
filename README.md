# GoSport - A08 PBP

## Anggota Kelompok
- Carmella Geraldine Sutrisna
- Sherin Khaira Alya Mirabel
- Muhammad Yufan Jonni
- Johannes Nichola Simatupang
- Muhammad Ibaadi Ilmi

## Deskripsi Aplikasi
**GoSport** adalah situs e-commerce yang menjual berbagai **peralatan olahraga** seperti sepatu, raket, bola, dan perlengkapan gym. Aplikasi ini memudahkan pengguna untuk mencari, membandingkan, dan membeli produk olahraga dari berbagai kategori.
Tujuan utama kami adalah mendukung gaya hidup sehat masyarakat dengan menyediakan platform digital yang mudah digunakan dan informatif.

## Daftar Modul
1. Autentikasi + Dashboard Profile: Login, register. (Carmella)
   - Create: Simpan data user baru: username, password (hashed), dan role (pembeli atau penjual).
   - Read: Lihat data profile sendiri.
   - Update: Ubah username dan/atau password.
   - Delete: Hapus akun.
4. Produk: Menampilkan daftar produk olahraga (initial dataset 100+ produk). (Sherin)
   - Create: Tambah produk baru (nama produk, harga, kategori, thumbnail).
   - Read: Lihat daftar atau detail produk.
   - Update: Edit produk oleh penjual produk tsb atau admin.
   - Delete: Hapus produk oleh penjual produk tsb atau admin.
5. Keranjang Belanja: Menyimpan produk yang ingin dibeli pengguna sebelum checkout. (Johannes)
   - Create: Tambah produk ke keranjang (hanya untuk user dengan role pembeli).
   - Read: Lihat isi keranjang user (pembeli) tsb.
   - Update: Ubah jumlah item yang ingin dibeli di keranjang.
   - Delete: Hapus item dari keranjang.
6. Pembayaran - Mengelola proses transaksi dan pembayaran. (Ilmi)
   - Create: Buat pesanan baru saat checkout.
   - Read: Lihat detail transaksi.
   - Update: Update status pembayaran.
   - Delete: Batalkan pembayaran.
7. Ulasan Produk - Pengguna dapat memberi rating dan review pada produk. (Yufan)
   - Create: Tambah ulasan & rrating (bintang 1-5) produk.
   - Read: Lihat daftar ulasan produk.
   - Update: Edit ulasan yang diberi user (pembeli) tsb.
   - Delete: Hapus ulasan.

## Sumber Dataset
Dataset awal diambil dari [Kaggle](https://www.kaggle.com/datasets/shouvikdey21/sports-ecommerce-products-dataset) — *Sports ECommerce Products Dataset* 

Dataset mencakup 100+ produk olahraga dengan atribut seperti:
- Product Name: Nama produk olahraga.
- Old Price: Harga asli produk sebelum diskon.
- Special Price: Harga produk setelah diskon diterapkan.
- Discount: Persentase potongan harga dari harga asli.
- Product: Kategori atau jenis produk olahraga (misalnya: Sepatu, Bola, Raket, dll).

## Jenis Pengguna
1. Admin - Mengelola data produk, transaksi, dan pengguna.
2. Pengguna Terdaftar - Dapat login, membeli produk, memberikan ulasan.
3. Pengunjung (Guest) - Dapat melihat produk tanpa login, tapi tidak bisa membeli.

## Link Deployment (PWS)
https://pbp.cs.ui.ac.id/sherin.khaira/football-site
