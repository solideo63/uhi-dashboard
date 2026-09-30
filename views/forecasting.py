"""Prediksi tersimpan model terbaik, evaluasi delapan model, dan proyeksi LST."""
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import uhi_data as data
import uhi_forecast as forecast
import uhi_model as model
import uhi_ui as ui
import uhi_viz as viz
from uhi_peta_forecast import peta_forecasting

ui.judul_halaman(
    "Regresi machine learning", "Forecasting LST",
    "Prediksi LST 2024 dari model terbaik hasil run ulang data lama. "
    "Bandingkan suhu aktual, prediksi, dan selisihnya pada grid Jakarta.",
)

try:
    info, evaluasi, seluruh_prediksi = forecast.muat_hasil()
except (FileNotFoundError, ValueError, AssertionError) as error:
    st.error(str(error))
    st.stop()

pred_uji = seluruh_prediksi[seluruh_prediksi["split"].eq("test")].copy()
metrik = model.metrik(pred_uji["aktual"], pred_uji["prediksi"], info["n_features"])
nama_algoritma = {"RF": "Random Forest", "SVR": "Support Vector Regression"}[info["best_algorithm"]]
label_model = f"{info['best_model']} – {info['best_algorithm']}"
ui.kartu([
    ("Model terbaik penelitian", label_model, nama_algoritma),
    ("R² data uji", f"{metrik['R2']:.4f}", "Evaluasi run ulang M4-RF"),
    ("RMSE data uji", f"{metrik['RMSE']:.4f} °C", f"MAE {metrik['MAE']:.4f} °C"),
    ("Grid uji", str(len(pred_uji)), f"{info['n_train']} grid latih · {info['n_features']} fitur"),
])
tab_prediksi, tab_resmi, tab_proyeksi = st.tabs(["Model terbaik & peta", "Evaluasi model", "Proyeksi LST"])

with tab_prediksi:
    st.caption(
        f"{info['best_label']} — {nama_algoritma}. Prediksi utama berasal dari hasil notebook. "
        "Grid dengan indeks interpolasi diprediksi memakai model tersimpan, tanpa pelatihan ulang."
    )
    prediksi_peta = forecast.lengkapi_prediksi_peta(seluruh_prediksi)
    cakupan = st.radio("Cakupan peta", ["Data uji", "Seluruh grid tersedia"],
                       index=1, horizontal=True, key="forecast-cakupan")
    hanya_uji = cakupan == "Data uji"
    pred = pred_uji if hanya_uji else prediksi_peta
    if not hanya_uji:
        st.caption("Mencakup data latih, data uji, dan prediksi tambahan dengan NDVI/NDBI yang diinterpolasi antartahun. Kartu metrik tetap dihitung hanya dari data uji.")
    pilihan = st.radio("Nilai pada peta", ["Prediksi − aktual", "LST prediksi 2024", "LST aktual 2024"],
                        horizontal=True, key="forecast-peta")
    kolom = {"Prediksi − aktual": "selisih", "LST prediksi 2024": "prediksi", "LST aktual 2024": "aktual"}[pilihan]
    peta_data = forecast.peta_prediksi(prediksi_peta, hanya_uji=hanya_uji)
    if kolom == "selisih":
        limit = max(float(pred["selisih"].abs().max()), .01)
        rentang = (-limit, limit)
        warna = ["#2166ac", "#f7f7f7", "#b2182b"]
    else:
        rentang = (float(pred[["aktual", "prediksi"]].min().min()),
                   float(pred[["aktual", "prediksi"]].max().max()))
        if rentang[0] == rentang[1]:
            rentang = (rentang[0]-.01, rentang[1]+.01)
        warna = viz.RAMPA["lst"]
    st.subheader(f"{pilihan} — Jakarta")
    st.markdown(viz.legenda_kontinu(pd.Series(rentang), warna, pilihan, " (°C)"), unsafe_allow_html=True)
    st_folium(peta_forecasting(peta_data, kolom, rentang, forecast.batas_jakarta()),
              width=None, height=540, returned_objects=[],
              key=f"forecast-map-{kolom}-{hanya_uji}-{info['created_utc']}")
    st.caption(
        "Selisih = prediksi − aktual. Biru: prediksi lebih dingin; merah: lebih panas; "
        "putih: mendekati aktual. Grid abu-abu berada di luar cakupan tampilan atau tidak memiliki data lengkap. "
        "Peta aktual dan prediksi memakai rentang warna yang sama."
    )
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.plotly_chart(viz.sebar_prediksi(pred_uji["aktual"], pred_uji["prediksi"],
                        f"Aktual vs prediksi data uji — {label_model}", viz.RAMPA["lst"][2]), width="stretch")
    with right:
        st.subheader("Selisih pada data uji")
        ui.kartu([
            ("Bias rata-rata", f"{pred_uji['selisih'].mean():+.3f} °C", "prediksi − aktual"),
            ("Galat mutlak terbesar", f"{pred_uji['selisih'].abs().max():.3f} °C", "pada grid uji"),
        ])
        per_klaster = (pred_uji.assign(galat=pred_uji["selisih"].abs()).groupby("cluster")
                       .agg(Grid=("grid_id", "size"), MAE=("galat", "mean"), Bias=("selisih", "mean"))
                       .reset_index().rename(columns={"cluster": "Klaster"}))
        st.dataframe(per_klaster.style.format({"MAE": "{:.3f} °C", "Bias": "{:+.3f} °C"}),
                     hide_index=True, width="stretch")
    with st.expander("Prediksi dan selisih tiap grid"):
        detail = pred[["grid_id", "cluster", "split", "aktual", "prediksi", "selisih"]].rename(columns={
            "grid_id": "Grid", "cluster": "Klaster", "split": "Sampel", "aktual": "Aktual (°C)",
            "prediksi": "Prediksi (°C)", "selisih": "Prediksi − aktual (°C)"})
        st.dataframe(detail.style.format({"Aktual (°C)": "{:.3f}", "Prediksi (°C)": "{:.3f}",
                      "Prediksi − aktual (°C)": "{:+.3f}"}), hide_index=True, width="stretch")
        st.download_button("Unduh prediksi dan selisih", pred.to_csv(index=False).encode("utf-8"),
                           file_name=f"prediksi_selisih_{info['best_model']}_{info['best_algorithm']}.csv", mime="text/csv")

with tab_resmi:
    st.subheader("Hasil penelitian pada Excel")
    excel = pd.read_excel(data.DATA / 'Hasil Evaluasi Cluster.xlsx', sheet_name='Sheet4', nrows=8)
    excel.columns = excel.columns.str.strip()
    excel['Test_R2'] = pd.to_numeric(excel['Test_R2'], errors='raise')
    best_excel = excel.loc[excel['Test_R2'].idxmax()]
    st.info(f"Excel: {best_excel['Config'].strip()} — {best_excel['Algorithm'].strip()}; "
            f"R² uji {best_excel['Test_R2']:.4f}, RMSE {float(best_excel['Test_RMSE']):.4f} °C. "
            "Peta memakai prediksi run ulang yang tersimpan, bukan prediksi dari tabel Excel.")
    st.dataframe(excel[['Config', 'Algorithm', 'Test_R2', 'Test_RMSE', 'Test_MAE']],
                 hide_index=True, width="stretch")
    st.subheader("Evaluasi run ulang data lama")
    st.caption("M1/M2 memakai lima lag LST. M3/M4 menambahkan NDVI dan NDBI 2009–2024, "
               "termasuk 2024. M2/M4 dilatih terpisah per klaster. Semua model memakai grid uji yang sama.")
    tabel = evaluasi[["Config", "Algorithm", "N_Features", "Train_R2", "Test_R2", "Test_RMSE",
                      "Test_MAE", "Test_MAPE", "CV_R2_Mean", "CV_R2_Std"]].rename(columns={
        "Config": "Konfigurasi", "Algorithm": "Algoritma", "N_Features": "Fitur",
        "Train_R2": "R² latih", "Test_R2": "R² uji", "Test_RMSE": "RMSE (°C)",
        "Test_MAE": "MAE (°C)", "Test_MAPE": "MAPE (%)", "CV_R2_Mean": "CV R² rerata",
        "CV_R2_Std": "CV R² simpangan"})
    st.dataframe(tabel.style.format({column: "{:.4f}" for column in tabel.columns[3:]})
                 .highlight_max(subset=["R² uji"], color="#e4f2e2")
                 .highlight_min(subset=["RMSE (°C)", "MAE (°C)"], color="#e4f2e2"),
                 hide_index=True, width="stretch")
    st.caption("M4-RF ditetapkan sebagai model utama penelitian. Nilai evaluasi run ulang "
               "ditampilkan apa adanya; CV dihitung hanya pada data latih.")
    st.download_button("Unduh evaluasi model", evaluasi.to_csv(index=False).encode("utf-8"),
                       file_name="evaluasi_model_data_lama.csv", mime="text/csv")
    with st.expander("Sumber dan periode analisis"):
        st.write("Data indeks: FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson, sebelum penyesuaian sensor.")
        st.write(f"Run: {info['created_utc']} · {info['n_complete']} grid lengkap · target LST 2024.")

# --- Tab 3: proyeksi rekursif ke periode berikutnya ------------------------

with tab_proyeksi:
    ui.keterangan(
        "Proyeksi <b>2027</b> memakai model <b>M4-Random Forest</b>: lag LST, NDVI, "
        "dan NDBI, dengan model terpisah per klaster. Jendela fitur digeser tiga tahun; "
        "<b>NDVI dan NDBI 2027 diasumsikan tetap seperti 2024</b>. "
        "Hasil ini merupakan proyeksi bersyarat pada asumsi tersebut."
    )
    algoritma_proyeksi = "M4-Random Forest"
    langkah = 1
    ramalan = forecast.proyeksi_m4()

    panel = data.muat_panel()
    riwayat = (
        panel.dropna(subset=["lst", "k-means_cluster"])
        .assign(cluster=lambda d: d["k-means_cluster"].astype(int))
        .groupby(["tahun", "cluster"])["lst"]
        .mean()
        .reset_index()
    )
    proyeksi = ramalan.groupby(["tahun", "cluster"])["lst"].mean().reset_index()
    proyeksi["cluster"] = proyeksi["cluster"].astype(int)

    tahun_akhir = int(proyeksi["tahun"].max())
    kota_sekarang = riwayat[riwayat["tahun"] == data.TAHUN[-1]]["lst"].mean()
    kota_nanti = proyeksi[proyeksi["tahun"] == tahun_akhir]["lst"].mean()

    ui.kartu(
        [
            ("Rata-rata klaster 2024", f"{kota_sekarang:.2f} °C", "nilai teramati"),
            ("Proyeksi " + str(tahun_akhir), f"{kota_nanti:.2f} °C", f"{kota_nanti - kota_sekarang:+.2f} °C"),
            ("Horizon", f"{tahun_akhir - data.TAHUN[-1]} tahun", f"{langkah} periode ke depan"),
            ("Dasar proyeksi", "M4-RF", "Lag LST + NDVI + NDBI + klaster"),
        ]
    )

    st.plotly_chart(
        viz.garis_forecast(
            riwayat,
            proyeksi,
            "cluster",
            f"LST historis dan proyeksi tiap klaster — {algoritma_proyeksi}",
        ),
        width="stretch",
    )

    st.subheader("Nilai proyeksi tiap klaster")
    tabel_proyeksi = (
        pd.concat([riwayat.assign(jenis="Historis"), proyeksi.assign(jenis="Proyeksi")])
        .pivot_table(index="cluster", columns="tahun", values="lst")
        .reset_index()
        .rename(columns={"cluster": "Klaster"})
    )
    tabel_proyeksi.columns = [
        c if isinstance(c, str) else f"{c}{' (proyeksi)' if c > data.TAHUN[-1] else ''}"
        for c in tabel_proyeksi.columns
    ]
    st.dataframe(
        tabel_proyeksi.style.format(
            {c: "{:.2f}" for c in tabel_proyeksi.columns if c != "Klaster"}
        ),
        hide_index=True,
        width="stretch",
    )

    with st.expander("Lihat proyeksi tiap grid"):
        detail = ramalan.rename(
            columns={"grid_id": "Grid", "tahun": "Tahun", "lst": "LST proyeksi (°C)", "cluster": "Klaster"}
        )
        st.dataframe(
            detail.style.format({"LST proyeksi (°C)": "{:.2f}"}),
            hide_index=True,
            width="stretch",
            height=340,
        )
        st.download_button(
            "Unduh CSV",
            ramalan.to_csv(index=False).encode("utf-8"),
            file_name="proyeksi_lst.csv",
            mime="text/csv",
        )
