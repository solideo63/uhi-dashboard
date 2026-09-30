"""Beranda: ringkasan penelitian, cakupan data, dan hasil utamanya."""

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import uhi_data as data
import uhi_ui as ui
import uhi_viz as viz

ui.judul_halaman(
    "Beranda",
    "Ringkasan Penelitian",
    "Dashboard ini menyajikan visualisasi spasio-temporal <b>Land Surface Temperature</b> (LST), "
    "<b>Normalized Difference Vegetation Index</b> (NDVI), dan "
    "<b>Normalized Difference Built-up Index</b> (NDBI) pada grid 1 × 1 km di DKI Jakarta, "
    "beserta hasil <i>time series clustering</i>, peramalan LST berbasis <i>machine learning</i>, "
    "dan interpretasinya dengan SHAP. Seluruh nilai LST merupakan komposit citra pada puncak "
    "musim kemarau tiap periode pengamatan.",
)

panel = data.muat_panel()
matriks = data.matriks_lst()

lst_awal = matriks[data.TAHUN[0]].mean()
lst_akhir = matriks[data.TAHUN[-1]].mean()
lst_puncak = matriks.mean().idxmax()

ui.kartu(
    [
        ("Grid pengamatan", f"{len(data.muat_grid()):,}".replace(",", "."), "sel 1 × 1 km"),
        ("Periode", f"{len(data.TAHUN)}", f"{data.TAHUN[0]}–{data.TAHUN[-1]}, interval 3 tahun"),
        ("Rata-rata LST 2024", f"{lst_akhir:.2f} °C", f"{lst_akhir - lst_awal:+.2f} °C terhadap {data.TAHUN[0]}"),
        ("LST tertinggi", f"{matriks[lst_puncak].mean():.2f} °C", f"tercatat pada periode {lst_puncak}"),
        ("Klaster", "4", "tiga metode clustering"),
    ]
)

kiri, kanan = st.columns([3, 2], gap="large")

with kiri:
    st.subheader("Perkembangan LST")
    ringkas = panel.groupby("tahun")[["lst"]].mean().reset_index()
    st.plotly_chart(
        viz.garis_tren(
            ringkas,
            "tahun",
            {"LST": "lst"},
            "Rata-rata LST DKI Jakarta pada puncak kemarau",
            "LST (°C)",
        ),
        width="stretch",
    )

with kanan:
    st.subheader("Hasil utama")

    evaluasi_cluster = data.muat_evaluasi_cluster()
    pada_k4 = evaluasi_cluster[evaluasi_cluster["k"] == 4]
    terbaik_cluster = pada_k4.loc[pada_k4["silhouette"].idxmax()]

    evaluasi_model = data.muat_evaluasi_model()
    terbaik_model = evaluasi_model.loc[(evaluasi_model["model"] == "M4") & (evaluasi_model["algoritma"] == "RF")].iloc[0]

    shap_m4 = data.muat_shap_ringkas().query("kode == 'M4'").set_index("variabel")["kontribusi"]

    st.markdown(
        f"""
**Metode clustering terbaik pada k = 4**

`{terbaik_cluster['metode']}` — Silhouette **{terbaik_cluster['silhouette']:.4f}**,
Davies–Bouldin **{terbaik_cluster['db_index']:.4f}**, Dunn **{terbaik_cluster['dunn_index']:.4f}**,
WCSS **{terbaik_cluster['wcss']:.2f}**.

**Model peramalan terbaik**

`{terbaik_model['konfigurasi']}` dengan algoritma **{terbaik_model['algoritma']}** —
R² uji **{terbaik_model['test_r2']:.4f}**, Adjusted R² **{terbaik_model['test_adj_r2']:.4f}**,
RMSE **{terbaik_model['test_rmse']:.4f} °C**, MAE **{terbaik_model['test_mae']:.4f} °C**,
MAPE **{terbaik_model['test_mape'] * 100:.2f}%**.

**Penjelas utama prediksi menurut SHAP**

Riwayat LST menyumbang **{shap_m4.get('LST', 0):.1f}%** penjelasan, NDBI
**{shap_m4.get('NDBI', 0):.1f}%**, dan NDVI **{shap_m4.get('NDVI', 0):.1f}%**, sehingga
variabel lingkungan secara keseluruhan mengambil
**{shap_m4.get('NDBI', 0) + shap_m4.get('NDVI', 0):.1f}%**.
"""
    )

st.divider()

# --- Intensitas Urban Heat Island ------------------------------------------

st.subheader("Intensitas Urban Heat Island")
ui.keterangan(
    "Intensitas UHI tiap grid dihitung sebagai selisih suhu permukaannya terhadap "
    "rata-rata suhu permukaan seluruh grid di zona rural, yang dipakai sebagai keadaan "
    "acuan tanpa pengaruh perkotaan. Wilayah kajian dibagi menjadi tiga zona berdasarkan "
    "jarak dari batas wilayah administrasi DKI Jakarta."
)
st.latex(r"UHI_i = T_i - \bar{T}_s")
ui.keterangan(
    "dengan <b>UHI<sub>i</sub></b> intensitas SUHI pada grid ke-i (°C), "
    "<b>T<sub>i</sub></b> LST pada grid ke-i (°C), dan "
    "<b>T̄<sub>s</sub></b> rata-rata LST seluruh grid pada zona rural (°C)."
)

uhi = data.muat_uhi()
ringkas_uhi = data.ringkas_uhi().set_index("zona")
komposisi_uhi = data.komposisi_kelas_uhi()
jumlah_kelas = uhi["klas_uhi"].value_counts()

KELAS_PANAS = ["Strong", "Extreme"]
panas = int(jumlah_kelas.get("Strong", 0) + jumlah_kelas.get("Extreme", 0))
urban_kuat = uhi[(uhi["zona"] == "urban") & (uhi["klas_uhi"].isin(KELAS_PANAS))]
rural_kuat = uhi[(uhi["zona"] == "rural") & (uhi["klas_uhi"].isin(KELAS_PANAS))]

ui.kartu(
    [
        (
            "Rata-rata UHI urban",
            f"{ringkas_uhi.loc['urban', 'rata']:+.2f} °C",
            f"median {ringkas_uhi.loc['urban', 'median']:+.2f} °C, maksimum {ringkas_uhi.loc['urban', 'maksimum']:+.2f} °C",
        ),
        (
            "Rata-rata UHI peri-urban",
            f"{ringkas_uhi.loc['peri-urban', 'rata']:+.2f} °C",
            f"penyangga 0–10 km, {int(ringkas_uhi.loc['peri-urban', 'grid'])} grid",
        ),
        (
            "Zona acuan rural",
            "0,00 °C",
            f"penyangga 10–25 km, {int(ringkas_uhi.loc['rural', 'grid'])} grid",
        ),
        (
            "Grid Strong & Extreme",
            f"{panas}",
            f"{panas / len(uhi) * 100:.1f}% dari {len(uhi)} grid kajian",
        ),
        (
            "Grid urban Strong & Extreme",
            f"{len(urban_kuat) / int(ringkas_uhi.loc['urban', 'grid']) * 100:.1f}%",
            f"{len(urban_kuat)} dari {int(ringkas_uhi.loc['urban', 'grid'])} grid Jakarta",
        ),
    ]
)

peta_uhi_kol, tabel_uhi_kol = st.columns([3, 2], gap="large")

with peta_uhi_kol:
    st.markdown("###### Sebaran intensitas UHI")
    st.markdown(viz.legenda_uhi(jumlah_kelas), unsafe_allow_html=True)
    st_folium(
        viz.peta_uhi(uhi),
        width=None,
        height=520,
        returned_objects=[],
        key="peta-uhi",
    )
    st.caption(
        "Garis hitam menandai batas wilayah administrasi DKI Jakarta. "
        "Arahkan kursor ke sebuah sel untuk membaca zona dan intensitasnya."
    )

with tabel_uhi_kol:
    st.markdown("###### Klasifikasi intensitas UHI")
    klasifikasi = pd.DataFrame(
        {
            "Intensitas UHI": [data.RENTANG_UHI[k] for k in data.KELAS_UHI],
            "Kategori": data.KELAS_UHI,
            "Jumlah grid": [int(jumlah_kelas.get(k, 0)) for k in data.KELAS_UHI],
            "Porsi": [jumlah_kelas.get(k, 0) / len(uhi) * 100 for k in data.KELAS_UHI],
        }
    )
    st.dataframe(
        klasifikasi.style.format({"Porsi": "{:.1f}%"}),
        hide_index=True,
        width="stretch",
    )

    st.markdown("###### Susunan kelas tiap zona")
    st.plotly_chart(
        viz.komposisi(
            komposisi_uhi.assign(zona=lambda d: d["zona"].astype(str)),
            "zona",
            "klas_uhi",
            "persen",
            viz.WARNA_UHI,
            "Porsi kelas intensitas UHI di tiap zona",
            "Porsi grid dalam zona (%)",
        ),
        width="stretch",
    )

ui.keterangan(
    f"Zona urban rata-rata <b>{ringkas_uhi.loc['urban', 'rata']:+.2f} °C</b> lebih panas "
    f"daripada acuan rural, dan zona peri-urban "
    f"<b>{ringkas_uhi.loc['peri-urban', 'rata']:+.2f} °C</b>, sehingga intensitas UHI "
    "meluruh secara teratur seiring bertambahnya jarak dari pusat kota. "
    f"Sebanyak <b>{len(urban_kuat)} dari {int(ringkas_uhi.loc['urban', 'grid'])} grid</b> "
    "di dalam wilayah administrasi Jakarta tergolong Strong atau Extreme.",
)
ui.keterangan(
    "Dua hal perlu diperhatikan saat membacanya. <b>Pertama</b>, zona ditentukan murni "
    "oleh jarak dari batas administrasi, bukan oleh tutupan lahannya, sehingga "
    f"<b>{len(rural_kuat)} grid</b> di zona rural tetap tergolong Strong atau Extreme — umumnya kawasan terbangun "
    "di luar Jakarta seperti Tangerang, Bekasi, dan Depok. "
    "<b>Kedua</b>, komposit citra untuk analisis ini diambil pada Oktober 2024, berbeda "
    "dari komposit Juli–Agustus yang dipakai halaman lain, sehingga nilai LST-nya tidak "
    "dapat dibandingkan langsung dengan angka pada halaman Eksplorasi.",
    samping=True,
)

st.divider()

st.subheader("Isi dashboard")
ui.kartu_isi(
    [
        ("Eksplorasi", "Peta grid per tahun untuk LST, NDVI, atau NDBI, disertai statistik dan distribusinya."),
        ("Perubahan Temporal", "Tren rata-rata tiap variabel, selisih antarperiode, dan korelasi LST dengan NDVI serta NDBI."),
        ("Clustering", "Peta klaster tiga metode, pola LST tiap klaster, dan perbandingan evaluasinya."),
        ("Forecasting", "Evaluasi Random Forest dan SVR, sebaran prediksi per grid, serta proyeksi LST ke depan."),
        ("Interpretasi SHAP", "Kontribusi LST, NDVI, dan NDBI terhadap prediksi, antarmodel maupun antarklaster."),
    ]
)

st.divider()

bawah_kiri, bawah_kanan = st.columns([3, 2], gap="large")

with bawah_kiri:
    st.subheader("Cakupan data")
    sensor = data.sensor_per_tahun()
    cakupan = pd.DataFrame(
        {
            "Tahun": data.TAHUN,
            "Jendela komposit": [data.JENDELA_BULAN[t] for t in data.TAHUN],
            "Satelit NDVI/NDBI": [sensor.get(t, "—") for t in data.TAHUN],
            "Grid dengan LST": [int(panel[panel["tahun"] == t]["lst"].notna().sum()) for t in data.TAHUN],
            "Grid dengan NDVI": [int(panel[panel["tahun"] == t]["ndvi"].notna().sum()) for t in data.TAHUN],
            "Grid dengan NDBI": [int(panel[panel["tahun"] == t]["ndbi"].notna().sum()) for t in data.TAHUN],
        }
    )
    st.dataframe(cakupan, hide_index=True, width="stretch")

    kosong_indeks = int(panel["ndvi"].isna().sum())
    ui.keterangan(
        "Tiga hal perlu diperhatikan saat membaca seluruh halaman. "
        f"<b>Pertama</b>, {len(data.muat_grid()) - len(matriks)} grid tidak memiliki nilai LST "
        "sama sekali sehingga tidak diikutkan dalam clustering maupun pemodelan; jumlah grid "
        f"yang dianalisis adalah {len(matriks)} dari {len(data.muat_grid())}. "
        f"<b>Kedua</b>, {kosong_indeks} sel tidak memperoleh citra bebas awan untuk NDVI dan NDBI; "
        "peta menggambarnya abu-abu, sedangkan pemodelan mengisinya dengan interpolasi "
        "antartahun. "
        "<b>Ketiga</b>, satelit sumber NDVI dan NDBI berganti antarperiode dari Landsat 7 ke "
        "Landsat 8 lalu Sentinel-2, sehingga lompatan nilai yang bertepatan dengan pergantian "
        "itu perlu diperiksa lebih dulu terhadap kemungkinan pengaruh perbedaan sensor.",
        samping=True,
    )

with bawah_kanan:
    st.subheader("Sumber data")
    st.markdown(
        """
- `LSTPuncakKemarau.geojson` — LST puncak kemarau per grid per periode
- `FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson` — NDVI dan NDBI seluruh periode, sekaligus sumber geometri grid
- `cluster_spatial_k4.geojson` — label klaster k = 4 untuk tiga metode
- `Hasil Evaluasi Cluster.xlsx` — evaluasi clustering dan evaluasi model
- `tabel_vector_shap_summary.csv` dan dua berkas SHAP per klaster
"""
    )
    ui.keterangan(
        "Angka evaluasi clustering, evaluasi model, dan SHAP dibaca langsung dari berkas "
        "hasil penelitian, bukan dihitung ulang oleh dashboard."
    )
