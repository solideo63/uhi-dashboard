# Ekstraksi NDVI/NDBI dan prediksi LST 2024

**Panduan ini untuk versi penyesuaian Landsat yang kini diarsipkan sebagai
`New_LST_RF_SVR_Regression_Colab.landsat_v2.ipynb`.** Notebook aktif kembali
memakai data lama; lihat `PANDUAN_FORECASTING.md` untuk alur yang dipakai dashboard.

File utama:

- `ndvi_ndbi_jkt.js`: ekstraksi Earth Engine dengan grid 1 km dan sampling bersama 30 m.
- `New_LST_RF_SVR_Regression_Colab.ipynb`: notebook analisis mandiri, tanpa perlu mengunggah modul Python tambahan.
- `*.sebelum_perbaikan.*`: cadangan skrip dan notebook asli, termasuk hasil serta visualisasi terdahulu.

## Ketersediaan citra Landsat

Pencarian katalog publik Planetary Computer dilakukan untuk 1 Juni–30 September
pada kotak batas seluruh grid sumber. Angka berikut adalah **scene yang dikembalikan
katalog**, bukan jumlah piksel bebas awan, bukan pula jumlah tanggal unik.

| Tahun | Sensor | Scene Tier 1 | Scene dengan awan seluruh scene <50% | Tanggal unik setelah filter |
|---|---|---:|---:|---:|
| 2009 | Landsat 7 | 6 | 6 | 4 |
| 2012 | Landsat 7 | 9 | 8 | 4 |
| 2015 | Landsat 8 | 14 | 12 | 7 |
| 2018 | Landsat 8 | 16 | 14 | 8 |
| 2021 | Landsat 8 | 14 | 8 | 4 |
| 2024 | Landsat 8 | 16 | 10 | 6 |

Metadata scene ada di `audit_katalog_landsat.csv`; pencarian bisa diulang melalui
`cek_katalog_landsat.py`. Bounding box dapat memasukkan scene yang hanya mengenai
pinggiran area. Katalog Planetary Computer dan Earth Engine dapat berbeda isinya.
Karena itu, **kelengkapan spasial belum disimpulkan dari tabel ini**. Skrip GEE
menghitung scene yang benar-benar beririsan dengan asset Jakarta dan cakupan valid
setiap grid setelah masking; angka GEE menjadi acuan ekstraksi.

Sumber katalog: [STAC Planetary Computer](https://planetarycomputer.microsoft.com/docs/reference/stac/).

## Jalankan ekstraksi

1. Buka Google Earth Engine Code Editor dan tempel isi `ndvi_ndbi_jkt.js`.
2. Pastikan `CFG.jakartaAsset` bisa diakses. Jika tersedia, isi `CFG.gridAsset`
   dengan asset **grid penelitian yang sama** dengan data klaster/LST.
   Jika kosong, skrip membentuk grid memakai rumus identitas dari skrip lama.
3. Jalankan skrip. Periksa `Audit 2009` sampai `Audit 2024` di Console dan layer
   jumlah tanggal valid. Tidak ada pengisian lintas tahun ataupun fallback mosaic semu.
4. Jalankan **kedua Tasks** ekspor ke Drive:
   - `NDVI_NDBI_Grid1km_Jakarta_Landsat_OLIref_v2.geojson`
   - `audit_cakupan_landsat_v2.csv`
5. Hasil masuk folder `MyDrive/NDVI_NDBI_Jakarta_v2`. Periksa `n_grids_pass`,
   `n_grids_fail`, dan `valid_fraction` sebelum analisis.

Default revisi `obs_support_v3`: sedikitnya satu **tanggal** valid per piksel,
dan sedikitnya 80% luas bagian grid dalam Jakarta mempunyai piksel yang lolos.
Syarat sebelumnya dua tanggal menyebabkan seluruh grid 2009 gagal karena tahun
itu hanya memiliki dua tanggal citra di koleksi GEE. Ambang cakupan 80% tetap sama.
Ini kompromi dukungan temporal: satu pengamatan tidak memberikan ketahanan
komposit setara dengan beberapa pengamatan. Seluruh periode memakai konfigurasi
dan jendela Juni–September yang sama; tidak ada pengisian piksel buatan.

Untuk mengaudit kompromi ini, ekspor baru menyertakan `valid_fraction_ge1`,
`valid_fraction_ge2`, `single_obs_fraction`, dan `quality_ok_ge2` per grid.
Audit periode juga melaporkan jumlah grid yang tetap lolos bila memakai dua
pengamatan. Notebook menyimpan ringkasannya di `audit_dukungan_observasi.csv`.

Landsat 7 memiliki celah SLC-off; komposit multitemporal bisa membantu tetapi tidak
dijamin menutup semuanya. Nilai indeks grid yang gagal QA disimpan null.
`n_valid_pixels` menghitung piksel, `scene_count_aoi` menghitung scene seluruh AOI,
`unique_days_aoi` menghitung tanggal koleksi, dan `obs_mean` adalah rata-rata jumlah
tanggal valid per piksel dalam bagian grid di AOI (termasuk piksel dengan nol observasi).

## Penyesuaian sensor

Seri menggunakan Landsat 7 untuk 2009/2012 dan Landsat 8 untuk 2015–2024; Sentinel-2
tidak dipakai pada versi ini. Reflektansi Landsat 7 disesuaikan ke referensi OLI
**sebelum** menghitung indeks menggunakan transformasi RMA surface reflectance
Roy et al. (2016), Tabel 2, untuk red/NIR/SWIR1. Koefisien tidak diestimasi dari
data target LST. Keduanya memakai QA, rentang reflektansi, grid sampling, dan musim
yang sama. Mask bersama memastikan pembanding raw dan adjusted memakai piksel sama.

Koefisien literatur ini berasal dari wilayah/produk berbeda dan **belum divalidasi
lokal pada Jakarta Collection 2**. Output menandai `local_validation=not_performed`.
Ini bukan pipeline HLS lengkap, bukan koreksi BRDF, dan bukan bukti bahwa seluruh
efek sensor hilang. Kolom raw memungkinkan perbandingan sensitivitas tanpa
menghapus sinyal perubahan rata-rata antartahun melalui z-score.

Rujukan: [Roy et al. (2016), Tabel 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC6999663/),
[Landsat 7 Collection 2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LE07_C02_T1_L2),
[Landsat 8 Collection 2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).

## Jalankan notebook

1. Buka `New_LST_RF_SVR_Regression_Colab.ipynb` secara lokal (Jupyter/VS Code).
   Konfigurasi menunjuk `C:/Users/Solideo G. Bangun/uhi-dashboard/data`, termasuk
   ketika notebook dijalankan dari folder `sintaks`.
2. Indeks dibaca dari subfolder `data/NDVI_NDBI_Jakarta_v2`, klaster dari
   `data/cluster_spatial_k4.geojson`, dan LST dari `data/LSTPuncakKemarau.geojson`.
   Untuk Colab, salin folder `data` ke Drive dan sesuaikan `COLAB_DATA_DIR`;
   path Windows tidak dapat dibaca langsung dari runtime Colab. LST didukung sebagai
   CSV lebar (`lst_2009` ... `lst_2024` atau `lst_2024_EXCLUDED`) maupun GeoJSON
   panjang (`grid_id`, `period`, `mean`). Pastikan satuan LST sudah °C.
3. Jalankan seluruh sel. Pemeriksaan akan menolak data indeks lama, duplikat,
   periode hilang, skema/proyeksi salah, atau grid LST/klaster di luar grid indeks.
   Grid indeks tanpa label klaster/LST tetap dicatat di audit lalu dikeluarkan.
4. Output baru tersimpan di `data/output/regression_landsat_v2`.

Ekspor yang tersedia saat penyesuaian path mempunyai **0 dari 644 grid lolos
pada tahun 2009**. Notebook menampilkan dan menyimpan audit sebelum berhenti
karena tidak ada complete case lintas periode. Cakupan maksimum pada ekspor lama
adalah 79,86%, dengan syarat minimal dua pengamatan per piksel.

Untuk memakai revisi:

1. Tempel ulang skrip `ndvi_ndbi_jkt.js` terbaru ke Earth Engine (pastikan
   `minObservations: 1` dan `minValidFraction: 0.80`).
2. Jalankan dan selesaikan **kedua Tasks** ekspor. Periksa jumlah grid lolos
   2009 pada audit baru; kelulusan belum bisa dijamin sebelum dihitung ulang.
3. Unduh dan **ganti** dua file lama dalam `data/NDVI_NDBI_Jakarta_v2`.
   Ekspor baru mempunyai `processing_revision=obs_support_v3` dan
   `min_observations=1`. Hindari memakai salinan lama dengan nama yang sama di Drive.
4. Restart Kernel dan Run All notebook.

Mengubah ambang dalam notebook saja tidak mengembalikan NDVI/NDBI yang sudah
disimpan null. Jika ekspor baru masih tidak menghasilkan complete case, periksa
audit lagi sebelum mempertimbangkan perubahan sumber atau jendela pengamatan.

**NDVI dan NDBI 2024 tetap menjadi variabel independen pada M3/M4.** Totalnya 17
fitur: lima lag LST (2009–2021) ditambah enam periode NDVI dan enam periode NDBI
(2009–2024). LST 2024 sendiri hanya menjadi target, bukan fitur. Karena indeks
2024 dipakai, model ini memerlukan ketersediaan indeks 2024 saat melakukan prediksi.
Istilah forecasting dalam penelitian perlu menyebutkan kondisi tersebut.

M2/M4 memakai model terpisah per klaster. Semua konfigurasi memakai grid holdout
yang sama. CV berlangsung hanya pada data latih dan benar-benar mengikuti
konfigurasi per klaster. Parameter StandardScaler SVR di-fit ulang dalam setiap
fold; parameter model akhir disimpan di `standardisasi_svr_data_latih.csv`.
RF menggunakan indeks dalam skala asli setelah penyesuaian sensor.

Data yang tidak lengkap dikeluarkan secara eksplisit dan daftar alasannya disimpan.
Tidak ada interpolasi antartahun; semua model/skenario memakai complete cases sama.
Model pilihan ditentukan oleh CV RMSE, bukan seleksi skor data uji.
Label klaster yang dimuat berasal dari penelitian: pembentukannya tetap perlu
dipastikan tidak memakai LST target. Holdout acak antargrid tidak mengukur kemampuan
forecast ke tahun baru dan dapat optimistis karena kedekatan spasial.

LST dapat mewakili bulan puncak kemarau sedangkan indeks mewakili Juni–September.
Samakan atau jelaskan perbedaan dukungan waktu ini dalam metode penelitian.

SHAP RF menggunakan model klaster yang sesuai untuk setiap grid. Kontribusi
kelompok LST/NDVI/NDBI dihitung melalui enumerasi koalisi dengan background data
latih, disertai pemeriksaan bahwa baseline + kontribusi = prediksi. Tidak ada klaim
bahwa penjumlahan SHAP per lag sama dengan Shapley kelompok.

## Verifikasi lokal

`test_notebook_ndvi.py` memeriksa notebook/JavaScript, menjalankan seluruh alur
notebook dengan fixture sintetis, menguji inklusi fitur 2024, statistik scaler
data latih, QA input, keselarasan holdout, serta local accuracy SHAP. Hasil fixture
tidak dipakai sebagai data penelitian. Eksekusi Earth Engine dan hasil ekspornya
tetap memerlukan akun/akses asset pengguna dan belum dijalankan dari workspace ini.

```powershell
.\.venv\Scripts\python.exe sintaks\test_notebook_ndvi.py
```
