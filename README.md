# Dashboard Urban Heat Island DKI Jakarta

Dashboard Streamlit untuk visualisasi spasio-temporal LST, NDVI, dan NDBI pada grid
1 × 1 km di DKI Jakarta, hasil *time series clustering*, serta peramalan LST berbasis
*machine learning*.

## Menjalankan

```powershell
cd "C:\Users\Solideo G. Bangun\uhi-dashboard"
.\.venv\Scripts\streamlit.exe run app.py
```

Dashboard terbuka di <http://localhost:8501>. Menghentikannya dengan `Ctrl+C`.

Bila lingkungan virtual belum ada:

```powershell
C:\Python313\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe prep_data.py
```

## Isi halaman

Navigasi berada **di atas halaman**, bukan di bilah sisi, memakai
`st.navigation(..., position="top")`. Bilah sisi dikosongkan dan disembunyikan supaya
peta dan grafik memakai seluruh lebar layar. `app.py` hanya mengatur navigasi; isi tiap
halaman ada di `views/`.

| Halaman | Isi |
| --- | --- |
| **Beranda** | Ringkasan penelitian, tren LST, **intensitas UHI per zona penyangga**, cakupan data, dan hasil terbaik. |
| **Eksplorasi Spasio-Temporal** | Peta grid per tahun untuk LST, NDVI, atau NDBI, dengan statistik dan histogram. |
| **Analisis Perubahan Temporal** | Tren rata-rata tiap variabel, selisih antarperiode, dan korelasi LST dengan NDVI/NDBI. |
| **Time Series Clustering** | Peta klaster tiga metode, pola LST tiap klaster, evaluasi k = 2…7, dan tabel silang antarmetode. |
| **Forecasting LST** | Evaluasi resmi M1–M4 × RF/SVR, sebaran prediksi per grid, dan proyeksi LST ke periode berikutnya. |
| **Interpretasi SHAP** | Kontribusi LST, NDVI, dan NDBI terhadap prediksi, dibandingkan antarkonfigurasi model dan antarklaster. |

## Susunan berkas

```
uhi-dashboard/
├── app.py                       Router navigasi atas; tidak memuat isi halaman
├── views/                       Isi tiap halaman
│   ├── beranda.py
│   ├── eksplorasi.py
│   ├── temporal.py
│   ├── clustering.py
│   ├── forecasting.py
│   └── shap.py
├── uhi_data.py                  Pemuatan dan penggabungan data
├── uhi_viz.py                   Peta Folium dan grafik Plotly
├── uhi_model.py                 Random Forest dan SVR
├── uhi_ui.py                    Elemen antarmuka bersama
├── prep_data.py                 Ekstraksi Excel ke CSV (sekali jalan)
├── smoke_test.py                Uji seluruh modul di luar Streamlit
├── render_test.py               Uji tiap halaman merender tanpa galat
├── interaksi_test.py            Uji seluruh kombinasi kontrol
├── tangkap_layar.py             Tangkapan layar tiap halaman
├── tangkap_hover.py             Uji isi tooltip peta lewat kursor sungguhan
└── data/
    ├── LSTPuncakKemarau.geojson
    ├── NDVI_NDBI_SemuaTahun_Jakarta.geojson
    ├── cluster_spatial_k4.geojson
    ├── Hasil Evaluasi Cluster.xlsx
    └── evaluasi_cluster.csv, evaluasi_model.csv, definisi_model.csv
```

## Data

| Berkas | Isi |
| --- | --- |
| `LSTPuncakKemarau.geojson` | 3.864 fitur = 644 grid × 6 periode. Kolom `mean` berisi LST dalam °C. |
| `FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson` | 3.864 fitur = 644 grid × 6 periode, format panjang dengan kolom `year`, `NDVI`, `NDBI`, `sensor`, dan `count`. **Sumber NDVI/NDBI sekaligus sumber geometri grid.** |
| `cluster_spatial_k4.geojson` | 639 grid dengan label k = 4 untuk K-Means, DTW K-Means, dan k-Shape. |
| `Hasil Evaluasi Cluster.xlsx` | Evaluasi clustering k = 2…7 dan evaluasi model M1–M4 × RF/SVR. |
| `uhi_jabodetabek.geojson` | 4.088 grid Jabodetabek dengan zona penyangga, `uhi_intensity`, dan `klas_uhi`. Hanya periode Oktober 2024. |
| `batas/jakartacamat.shp` | 44 kecamatan DKI Jakarta; dipakai untuk menamai grid pada keterangan peta. |
| `batas/jabodetabek.shp` | 13 kabupaten dan kota se-Jabodetabek; cadangan untuk grid di luar DKI Jakarta. |
| `tabel_vector_shap_summary.csv` | Vector SHAP tiap konfigurasi model × variabel, porsi kontribusi, dan lag terkuat. |
| `true_vector_shap_cluster_M4_LagAll_byCluster.csv` | Sebaran vector SHAP per klaster × variabel untuk M4 (rata-rata, kuartil, median). |
| `true_vector_shap_cluster_M2_LagLST_byCluster.csv` | Sama untuk M2; hanya memuat LST sehingga porsinya selalu 100%. |

Periode pengamatan adalah **2009, 2012, 2015, 2018, 2021, 2024** dengan interval 3 tahun.

Berkas `NDVI_NDBI_SemuaTahun_Jakarta.geojson` yang masih ada di folder `data/` **sudah tidak
dipakai lagi**, digantikan oleh berkas `FINAL_...` di atas. Keduanya memuat 644 grid yang sama
dengan geometri yang identik secara geometris — simpangan bentuk 0 m dan selisih luas 0 m²,
hanya urutan simpul poligonnya yang berbeda — tetapi nilai indeksnya berbeda, sehingga berkas
`FINAL_` merupakan perhitungan yang direvisi, bukan salinan.

Kolom `year` pada berkas `FINAL_` tersimpan sebagai **teks**, bukan angka, dan diubah ke
bilangan bulat saat dimuat.

## Keterbatasan data yang perlu diketahui

1. **Satelit sumber NDVI dan NDBI berganti antarperiode**: Landsat 7 (2009, 2012),
   Landsat 8 (2015, 2018), Sentinel-2 (2021, 2024). Kedua lonjakan terbesar pada tren
   NDVI dan NDBI jatuh **tepat** pada titik pergantian itu. Pada NDBI lonjakan
   antarsatelit mencapai 0,058 sedangkan perubahan terbesar di dalam satelit yang sama
   hanya 0,007 — pola bertingkat yang merupakan ciri artefak sensor, bukan pertumbuhan
   lahan terbangun. Halaman Perubahan Temporal menandai titik peralihan itu dengan garis
   putus-putus dan menyatakan besarannya. **Tren NDVI dan NDBI antarperiode belum layak
   dipakai sebagai temuan sebelum nilainya diselaraskan antarsensor.**
2. **Dua sel pada periode 2012 tidak memperoleh citra bebas awan** (`count` = 0)
   sehingga NDVI dan NDBI-nya kosong; peta menggambarnya abu-abu dan pemodelan
   mengisinya dengan interpolasi antartahun.
2. **Lima grid tidak memiliki nilai LST sama sekali** sehingga tidak diikutkan dalam
   clustering maupun pemodelan. Jumlah grid yang dianalisis adalah 639.
3. **Jendela komposit citra berbeda antarperiode** (Agustus 2009; Juni–Agustus 2012;
   Agustus–September 2015 dan 2018; Agustus 2021; Juli–Agustus 2024), menyesuaikan
   ketersediaan citra bebas awan.
4. **Penomoran M1 dan M2 saling bertukar antara Sheet3 dan Sheet4** pada berkas Excel.
   Dashboard mengikuti penomoran tabel evaluasi (Sheet4) dan menandai perbedaannya.
5. **Analisis intensitas UHI memakai komposit Oktober 2024**, berbeda dari komposit
   Juli–Agustus yang dipakai halaman lain, dan hanya tersedia untuk satu periode.
   Nilai LST-nya karena itu tidak dapat dibandingkan langsung dengan halaman Eksplorasi.
6. **Zona penyangga ditentukan murni oleh jarak** dari batas administrasi, bukan oleh
   tutupan lahan. Karena itu 143 grid di zona rural tetap tergolong Strong atau Extreme,
   umumnya kawasan terbangun di Tangerang, Bekasi, dan Depok.

## Intensitas Urban Heat Island

Intensitas UHI tiap grid dihitung sebagai selisih LST-nya terhadap rata-rata LST seluruh
grid zona rural, `UHI_i = T_i − T̄_s`, lalu digolongkan ke lima kelas: `< 0 °C` No UHI,
`0–2 °C` Weak, `2–4 °C` Moderate, `4–6 °C` Strong, `> 6 °C` Extreme. Rumus dan batas kelas
ini diverifikasi ulang terhadap isi berkas dan cocok tepat.

Wilayah kajian dibagi tiga zona berdasarkan jarak dari batas DKI Jakarta: **urban**
(dalam wilayah administrasi, 639 grid), **peri-urban** (0–10 km, 1.141 grid), dan
**rural** (10–25 km, 2.308 grid) yang menjadi acuan.

## Catatan tentang angka evaluasi

Seluruh angka evaluasi clustering dan evaluasi model dibaca langsung dari
`Hasil Evaluasi Cluster.xlsx`, bukan dihitung ulang.

Tab **Sebaran prediksi** melatih ulang model saat aplikasi berjalan, karena berkas
hasil hanya menyimpan ringkasan metriknya sedangkan prediksi tiap grid diperlukan
untuk menggambar sebarannya. Penyetelan hiperparameter aslinya tidak tercatat, dan
hasil pelatihan ulang ini memberi R² sekitar 0,95–0,96 sementara berkas hasil mencatat
R² uji 0,74–0,83. Selisih sebesar itu kemungkinan besar berasal dari perbedaan cara
membagi data latih dan uji. **Angka yang dilaporkan sebagai hasil penelitian adalah
angka pada tab Evaluasi model**; tab Sebaran prediksi hanya untuk melihat pola galat
antargrid.

## Penamaan wilayah pada peta

Keterangan yang muncul saat kursor diarahkan ke sebuah sel menampilkan **nama kecamatan**,
bukan `grid_id` yang tidak berarti bagi pembaca. Nama itu tidak ditambahkan ke berkas data
mana pun: setiap kali aplikasi dijalankan, `uhi_data.wilayah_grid()` menghitungnya ulang
dengan menumpangtindihkan geometri grid terhadap batas administrasi, lalu memilih wilayah
yang **irisan luasnya paling besar** — bukan wilayah yang kebetulan memuat titik pusat sel.
Perhitungan memakai CRS metrik `EPSG:32748` supaya luasnya tidak bias, memerlukan sekitar
5 detik, lalu disimpan di penyangga Streamlit.

Cakupannya bertingkat karena ketersediaan datanya berbeda:

| Grid | Nama yang tampil |
| --- | --- |
| Di dalam DKI Jakarta (seluruh 644 grid) | `Kecamatan, Kota` — misalnya `Mampang Prapatan, Jakarta Selatan` |
| Di luar DKI Jakarta (3.357 grid) | Kabupaten atau kota saja — misalnya `Kota Tangerang`, karena batas kecamatan di luar Jakarta tidak tersedia |
| Di perairan Teluk Jakarta (66 grid) | `Perairan Teluk Jakarta` |

`grid_id` tetap dipertahankan pada tabel dan berkas unduhan karena diperlukan untuk
menggabungkan data antarberkas; yang diganti hanya keterangan pada peta.

## Pilihan desain

- **Warna klaster** memakai empat warna kategorikal (biru, oranye, aqua, violet) yang
  telah divalidasi keterbacaannya bagi penyandang buta warna pada seluruh pasangan
  warna, dan selalu didampingi legenda bernomor serta tabel.
- **LST, NDVI, dan NDBI** masing-masing memakai satu rona tunggal dari terang ke gelap,
  bukan pelangi, sehingga besaran terbaca dari kepekatan warnanya.
- **Keterangan skala peta digambar di atas peta**, bukan melayang di dalamnya, supaya
  petak di tepi atas tidak tertutup dan bentuknya seragam dengan keterangan peta klaster
  maupun peta UHI.
- **Warna variabel pada grafik SHAP** (LST, NDVI, NDBI) memakai biru/oranye/aqua, bukan
  merah/hijau/violet yang lebih intuitif secara semantik, karena pasangan merah–hijau
  gagal uji keterbacaan bagi penyandang buta warna deutan.
- **Tidak ada grafik dua sumbu.** Variabel dengan satuan berbeda ditampilkan terpisah.
- **Tema dikunci terang** karena palet warnanya divalidasi terhadap permukaan terang.
- **Navigasi di atas, bilah sisi disembunyikan**, sehingga peta grid 1 × 1 km dan grafik
  berdampingan memakai lebar penuh. Nama aplikasi disisipkan ke dalam bilah navigasi
  lewat CSS, karena apa pun yang digambar sebelum halaman dijalankan akan tertutup
  bilah navigasi yang melekat di atas layar.
- **Basemap Esri Light Gray** dipakai karena bebas kunci API; basemap CartoDB kini
  menuntut kunci dan menampilkan watermark.

## Pengujian

```powershell
.\.venv\Scripts\python.exe smoke_test.py       # seluruh modul
.\.venv\Scripts\python.exe render_test.py      # tiap halaman merender
.\.venv\Scripts\python.exe interaksi_test.py   # 30 kombinasi kontrol
```
