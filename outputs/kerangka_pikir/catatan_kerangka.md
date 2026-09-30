# Kerangka pikir berdasarkan dashboard

Kerangka ini mengikuti sumber aktif dashboard pada 30 September 2026. Penomoran tujuan mengikuti bagan awal: identifikasi pola, perbandingan model, dan interpretasi. Tidak ada perubahan pada aplikasi atau data.

## Narasi

Penelitian mengkaji variasi spasio-temporal suhu permukaan daratan (LST) di DKI Jakarta melalui integrasi riwayat suhu, indeks vegetasi (NDVI), dan indeks lahan terbangun (NDBI) pada grid 1 × 1 km. Data enam periode pengamatan, yaitu 2009, 2012, 2015, 2018, 2021, dan 2024, digunakan untuk mengeksplorasi distribusi dan perubahan kondisi termal serta mengelompokkan kemiripan deret waktu LST menggunakan K-Means Euclidean, DTW K-Means, dan k-Shape. Evaluasi klaster meliputi WCSS, Silhouette, Davies–Bouldin Index, dan Dunn Index. Label K-Means dengan empat klaster digunakan dalam pemodelan per klaster.

Perbandingan pemodelan disusun sebagai empat konfigurasi: M1 menggunakan riwayat LST secara global; M2 menggunakan riwayat LST dengan model terpisah per klaster; M3 menggunakan LST, NDVI, dan NDBI secara global; serta M4 menggunakan ketiga variabel dengan model terpisah per klaster. Setiap konfigurasi diuji menggunakan Random Forest dan Support Vector Regression. Evaluasi meliputi R², adjusted R², RMSE, MAE, MAPE, dan hasil validasi silang. Interpretasi SHAP menjelaskan kontribusi prediktor pada model Random Forest. Hasil spasial, evaluasi, dan interpretasi disintesiskan sebagai dasar pertimbangan wilayah prioritas kajian mitigasi panas perkotaan; prioritas tersebut merupakan usulan pemanfaatan hasil, bukan keluaran optimasi yang sudah dihitung dashboard.

## Ketepatan interpretasi

- Cakupan berbeda menurut tahap: 644 grid awal, 639 grid dengan LST lengkap untuk clustering, dan 637 complete cases regresi. Metadata run mencatat 509 grid latih serta 128 grid uji.
- M2/M4 melatih model terpisah per klaster. Label klaster bukan sekadar fitur numerik tambahan.
- M1/M2 menggunakan lima nilai LST 2009–2021. M3/M4 menambahkan enam periode NDVI dan enam periode NDBI, termasuk 2024, sehingga totalnya 17 fitur. Estimasi LST 2024 menggunakan indeks sezaman; hasilnya tidak boleh disebut peramalan murni hanya dari informasi sebelum 2024.
- Hasil run ulang: M3–SVR memiliki R² uji tertinggi (0,9520) dan RMSE terendah (0,1855 °C). M4–RF ditetapkan sebagai model utama dashboard, dengan R² 0,9398, RMSE 0,2078 °C dan MAE 0,1620 °C. Penetapan model utama berbeda dari pemeringkatan terbaik run ulang.
- Halaman SHAP masih membaca hasil arsip penelitian. Kontribusi M4–RF pada halaman itu adalah LST 57,34%, NDBI 25,62%, dan NDVI 17,03%; angka tersebut tidak boleh dipasangkan sebagai penjelasan SHAP hasil run ulang. Garis putus-putus dalam bagan menandai hubungan interpretatif dengan sumber hasil berbeda.
- Clustering pada deskripsi dashboard menggunakan enam periode, termasuk 2024. Karena itu, evaluasi belum membuktikan generalisasi temporal ke tahun baru. Untuk desain forecasting prospektif, pembentukan klaster dan seluruh prapengolahan perlu dibatasi pada informasi yang tersedia saat prediksi dibuat.
- Proyeksi 2027 menggeser jendela waktu dan mengasumsikan NDVI/NDBI 2027 tetap seperti 2024. Proyeksi ini merupakan skenario, bukan hasil validasi terhadap observasi 2027.
- Data aktif merupakan data sebelum harmonisasi antarsensor. Perubahan NDVI/NDBI lintas sensor perlu ditafsirkan dengan keterbatasan tersebut. SHAP menunjukkan kontribusi terhadap prediksi, bukan bukti sebab-akibat.
- Analisis intensitas UHI Jabodetabek merupakan konteks tambahan dengan cakupan/periode berbeda. Tidak dimasukkan sebagai prediktor regresi LST DKI Jakarta dalam bagan utama.

## Sumber lokal

- `uhi_data.py`: sumber indeks aktif, periode, panel dan label klaster.
- `views/clustering.py` dan `data/evaluasi_cluster.csv`: metode dan evaluasi klaster.
- `uhi_forecast.py`: sumber aktif `data/output/regression_legacy` dan asumsi proyeksi.
- `data/output/regression_legacy/best_model.json`: konfigurasi utama, fitur, jumlah sampel, metrik.
- `data/output/regression_legacy/summary_evaluation.csv`: perbandingan delapan kombinasi model–algoritma.
- `views/shap.py` dan `data/tabel_vector_shap_summary.csv`: sumber arsip dan kontribusi SHAP yang ditampilkan.

PNG untuk penyisipan dokumen, SVG untuk penyuntingan vektor, dan PDF untuk pencetakan tersedia dalam folder ini. `buat_bagan.py` dapat dijalankan kembali untuk memperbarui bagan.
