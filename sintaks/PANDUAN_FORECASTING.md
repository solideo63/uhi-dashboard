# Forecasting dengan data lama

Notebook aktif: `New_LST_RF_SVR_Regression_Colab.ipynb`.

## Input

Sel konfigurasi membaca folder `C:/Users/Solideo G. Bangun/uhi-dashboard/data`:

- `FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson`: data indeks lama yang aktif
  di dashboard sebelum penyesuaian antarsensor; bukan ekspor `NDVI_NDBI_Jakarta_v2`.
- `cluster_spatial_k4.geojson`: label klaster.
- `LSTPuncakKemarau.geojson`: LST aktual seluruh periode.

File yang lebih tua, `NDVI_NDBI_SemuaTahun_Jakarta.geojson`, mempunyai 600 grid
tanpa NDVI/NDBI 2018. Complete-case file itu hanya menyisakan 44 grid. File tersebut
tidak menjadi sumber run aktif ini. Tidak ada interpolasi untuk mengisi data kosong.

## Susunan kode

Notebook mempunyai satu rangkaian konfigurasi, pembacaan/pivot input, definisi
fitur, fungsi fit/predict/evaluasi, loop delapan model, ekspor, dan visualisasi.
Tidak ada lagi duplikasi blok SHAP atau pelatihan ulang untuk setiap grafik.
File awal lengkap disimpan di `*.sebelum_perbaikan.ipynb`. Versi penyesuaian
Landsat disimpan di `*.landsat_v2.ipynb`, beserta pengujian v2 yang terpisah.

NDVI/NDBI 2024 tetap termasuk dalam 17 prediktor M3/M4. M1/M2 hanya memakai lima
lag LST. Split acak 80:20 memakai seed 42. M2/M4 melatih model terpisah per klaster.
StandardScaler berada dalam pipeline SVR. Cross-validation memakai data latih
saja dan mengikuti model per klaster, bukan model global sebagai proxy.

Model untuk dashboard dipilih berdasarkan **R² data uji tertinggi**, sesuai kriteria
versi awal. Skor holdout tersebut bukan evaluasi independen tambahan setelah
pemilihan model; bukan pula evaluasi generalisasi temporal ke tahun baru.

## Menjalankan

Jalankan semua sel notebook, atau dari root proyek:

```powershell
.\.venv\Scripts\python.exe sintaks\jalankan_notebook_legacy.py
```

Runner menyimpan hasil eksekusi sel di notebook. Dependensi analisis: `matplotlib`,
`seaborn`, `nbclient`, `ipykernel`, `joblib`, serta pustaka data/model proyek.
Di Colab sesuaikan folder Drive pada konfigurasi; notebook tidak memerlukan modul
Python pendamping untuk menghitung model.

## Output dan dashboard

Hasil disimpan di `data/output/regression_legacy`:

- `summary_evaluation.csv`: delapan model.
- `all_predictions_test_set.csv`: prediksi semua model yang sejajar berdasarkan grid_id.
- `best_model.json`: model terpilih, metrik, jumlah sampel, kriteria, dan hash input.
- `best_model_predictions.csv` / `.geojson`: prediksi model terbaik, aktual,
  selisih, dan penanda latih/uji untuk setiap grid lengkap.
- `best_model.joblib`: model terlatih dan daftar fitur.
- Grafik evaluasi dan peta holdout.

`uhi_forecast.py` membaca dan memvalidasi hasil. Halaman `views/forecasting.py`
memakai prediksi tersimpan tersebut tanpa fallback pelatihan ulang.
Cache pembacaan diperbarui ketika file hasil berubah.

Tab peta default hanya menampilkan data uji. Pengguna dapat melihat seluruh grid,
dengan label data latih/uji di tooltip. Metrik evaluasi tetap hanya memakai data uji.
Peta aktual dan prediksi berbagi skala warna; peta **prediksi − aktual** memakai
skala simetris di sekitar nol. Biru berarti terlalu dingin, merah terlalu panas.
Grid yang tidak termasuk cakupan ditampilkan abu-abu. Proyeksi ke periode mendatang
tetap merupakan model lag LST terpisah, karena indeks masa depan belum tersedia.

## Perbandingan hasil penelitian dan run ulang

`Hasil Evaluasi Cluster.xlsx`, Sheet4, mencatat M4–RF sebagai R² uji tertinggi
(0,8340; RMSE 0,5092 °C). Ini berbeda dari hasil run ulang pada folder
`output/regression_legacy` (M3–SVR). Dashboard menampilkan kedua sumber secara
terpisah; peta tetap memakai prediksi per grid dari run ulang, bukan angka Excel.

Halaman SHAP memakai hasil RF penelitian lama. `tabel_vector_shap_summary.csv`
berisi agregasi jumlah nilai absolut SHAP per lag, dibuat sebelum sel terakhir.
`true_vector_shap_cluster_*.csv` berasal dari perhitungan koalisi kelompok
variabel pada sel terakhir notebook arsip. Kedua metode diberi label terpisah.
Grafik ringkasan menampilkan rata-rata ± simpangan baku dan proporsi kontribusi;
grafik True Vector SHAP menampilkan statistik per klaster.

Peta Forecasting berada di `uhi_peta_forecast.py`. Halaman mengimpor fungsi
langsung dari modul ini agar tetap dapat dibuka saat sesi Streamlit masih
menyimpan versi lama `uhi_viz`.

## Pengujian

Tab True Vector SHAP memakai **M3–RF tanpa klaster** untuk hasil global,
dengan 17 fitur LST, NDVI, dan NDBI. `sintaks/hitung_vector_shap_global.py`
menghitung nilai Shapley eksak dari seluruh delapan koalisi tiga kelompok
variabel, dengan baseline rata-rata fitur data uji mengikuti notebook arsip.
Jumlah kontribusi tiga kelompok diverifikasi sama dengan prediksi dikurangi
baseline. Prediksi dicocokkan
dengan CSV run ulang sebelum hasil SHAP diekspor. Pembacaan float memakai
`round_trip` untuk mempertahankan presisi saat mereproduksi pelatihan RF.
Hasil global ini diberi sumber tersendiri dari hasil per klaster penelitian lama.

```powershell
.\.venv\Scripts\python.exe test_forecasting_legacy.py
```

Pengujian memeriksa keselarasan prediksi dan geometri, tanda selisih, reproduksi
angka dengan model tersimpan, fitur 2024, hasil eksekusi notebook, serta kontrol
halaman Streamlit. Data input dan hasil versi lain tidak ditimpa.
