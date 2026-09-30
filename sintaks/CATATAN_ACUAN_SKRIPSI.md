# Acuan skripsi untuk notebook regresi dan SHAP

Notebook `New_LST_RF_SVR_Regression_Colab.ipynb` menggunakan
`MODE_ANALISIS = 'acuan_skripsi'` secara bawaan. Mode ini membaca dan
memvisualisasikan hasil penelitian tersimpan, bukan melatih model baru.

Sumber acuan yang telah dicocokkan dengan Skripsi Deo.docx:

- `data/Hasil Evaluasi Cluster.xlsx`, **Sheet4**, menjadi sumber utama
  evaluasi yang ditampilkan notebook. Seluruh sembilan kolom metrik untuk
  delapan konfigurasi/algoritma diperiksa terhadap `evaluasi_model.csv`.
  Sheet6 mengulang ringkasan hasil yang sama. Workbook tidak memuat data
  latih-uji, estimator, maupun nilai SHAP per observasi. Sheet3 berisi definisi
  M1/M2 yang tidak konsisten dengan Sheet4 dan skripsi terbaru, sehingga
  tidak digunakan sebagai definisi konfigurasi.
- `data/evaluasi_model.csv`: M4–RF R² 0,8340, RMSE 0,5092 °C,
  MAE 0,3840 °C. RMSE di skripsi dibulatkan menjadi 0,509 °C.
- `data/tabel_vector_shap_summary.csv`: M4–RF LST 57,34%,
  NDBI 25,62%, NDVI 17,03%; rata-rata absolut masing-masing
  0,64716, 0,28916, dan 0,19223 °C.
- `data/true_vector_shap_cluster_M4_LagAll_byCluster.csv`:
  ringkasan klaster dengan jumlah sampel 26, 28, 40, dan 34.

Notebook menguji kecocokan nilai acuan sebelum membuat grafik. Angka di atas
tidak ditulis sebagai keluaran estimator. Grafik, CSV, dan hash sumber acuan
disimpan dalam `data/output/acuan_skripsi`.

## Status reproduksi perhitungan

Reproduksi angka skripsi dari data mentah **belum terverifikasi**.
Kode pelatihan dan Vector SHAP tambahan tetap tersedia melalui
`MODE_ANALISIS = 'hitung_ulang'`; hasilnya disimpan dalam
`data/output/regression_reproduction` dan tidak menggantikan tabel acuan.

Temuan penelusuran:

1. `LSTPuncakKemarau.geojson`, sumber notebook perhitungan ulang, mempunyai
   rata-rata LST seluruh grid tahun 2024 sekitar 34,9624 °C.
2. Target 128 grid dalam `data/all_predictions_test_set.csv` cocok dengan
   `data/uhi di jakarta.geojson` (selisih numerik kurang dari 1e-10 °C),
   yang rata-rata LST seluruh grid tahun 2024-nya sekitar 38,9727 °C.
3. Prediksi M4–RF dalam arsip `data/all_predictions_test_set.csv` menghasilkan
   R² sekitar 0,797775 dan RMSE 0,547424 °C, sehingga arsip prediksi ini juga
   bukan bukti reproduksi tabel evaluasi skripsi R² 0,834.
4. Percobaan terbatas dengan sumber LST tersebut, parameter RF yang sudah
   tercatat (300 pohon, max_features='sqrt', seed 42), serta split 80/20
   terpisah per klaster menghasilkan jumlah uji sesuai skripsi, tetapi metrik
   belum identik. Tidak dilakukan pencarian seed untuk mengejar angka acuan.

Untuk menyelesaikan reproduksi dibutuhkan dataset eksperimen asli beserta
urutan/identitas grid latih-uji, notebook/model tersimpan asli, dan konfigurasi
SHAP yang menghasilkan tabel skripsi. Rata-rata prediksi E[f(X)] dan prediksi
pada rata-rata fitur f(E[X]) tidak diasumsikan sama. Ringkasan global dan per
klaster arsip juga tidak diasumsikan memakai agregasi/baseline identik tanpa
kode asalnya.

Cadangan notebook sebelum pengaturan acuan tersedia sebagai
`New_LST_RF_SVR_Regression_Colab.sebelum_acuan_skripsi.ipynb`.
