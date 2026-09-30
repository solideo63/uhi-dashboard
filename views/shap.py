"""Halaman interpretasi: kontribusi tiap variabel terhadap prediksi menurut SHAP."""

import streamlit as st
import plotly.graph_objects as go

import uhi_data as data
import uhi_ui as ui
import uhi_viz as viz

ui.judul_halaman(
    "Penjelas prediksi",
    "Interpretasi Model dengan SHAP",
    "Interpretasi Random Forest dari hasil penelitian lama. Ringkasan antar-model "
    "menjumlahkan nilai absolut SHAP seluruh lag per variabel. "
    "Nilai ringkasan menunjukkan besar kontribusi dalam °C, bukan arah perubahan suhu.",
)

WARNA_SHAP = {**viz.WARNA_VARIABEL, "LST": "#d73027"}

ringkas = data.muat_shap_ringkas()

terbaik = ringkas[ringkas["kode"] == "M4"]
porsi = terbaik.set_index("variabel")["kontribusi"]

ui.kartu(
    [
        ("Kontribusi LST", f"{porsi.get('LST', 0):.1f}%", "riwayat suhu grid itu sendiri"),
        ("Kontribusi NDBI", f"{porsi.get('NDBI', 0):.1f}%", "kerapatan lahan terbangun"),
        ("Kontribusi NDVI", f"{porsi.get('NDVI', 0):.1f}%", "kerapatan vegetasi"),
        (
            "Variabel lingkungan",
            f"{porsi.get('NDBI', 0) + porsi.get('NDVI', 0):.1f}%",
            "NDVI dan NDBI digabung, pada M4",
        ),
    ]
)
st.caption("Kartu merujuk SHAP M4–RF pada hasil penelitian lama (Excel, Sheet4), bukan perhitungan SHAP ulang.")

st.subheader("Porsi kontribusi tiap variabel per model")
st.plotly_chart(
    viz.komposisi(
        ringkas,
        "kode",
        "variabel",
        "kontribusi",
        WARNA_SHAP,
        "Kontribusi LST, NDVI, dan NDBI per model — Random Forest",
        "Kontribusi terhadap prediksi (%)",
        "Model",
    ),
    width="stretch",
)
ui.keterangan(
    "Setiap batang membandingkan komposisi kontribusi variabel pada model M1–M4. "
    "M1 dan M2 hanya memakai lag LST. M3 dan M4 menambahkan NDVI dan NDBI. "
    "Persentase menunjukkan porsi besar kontribusi SHAP, bukan arah perubahan suhu."
)
st.caption("Sumber: tabel_vector_shap_summary.csv — hasil SHAP penelitian tersimpan.")

st.subheader("Besar kontribusi dalam satuan suhu")
grafik_besaran = viz.besaran_shap(
    ringkas, "kode", "Rata-rata besar pengaruh tiap variabel", "Konfigurasi model"
)
grafik_besaran.update_traces(marker_color=WARNA_SHAP['LST'], selector=dict(name='LST'))
st.plotly_chart(grafik_besaran, width="stretch")
ui.keterangan(
    "Grafik ini memakai satuan asli, bukan persentase. Terlihat bahwa kontribusi LST "
    "menyusut dari 1,09 °C pada M1 menjadi 0,65 °C pada M4, sedangkan NDVI dan NDBI "
    "menambah pengaruh baru. Jadi porsi LST turun karena sebagian perannya diambil alih "
    "variabel lingkungan, bukan karena LST menjadi tidak penting."
)

st.subheader("Ringkasan SHAP: rata-rata, simpangan baku, dan proporsi")
pilihan = st.selectbox("Model Random Forest", list(ringkas['kode'].unique()), index=3,
                       key="shap-summary-model")
selected = ringkas[ringkas['kode'].eq(pilihan)].sort_values('shap_rata')
colors = [WARNA_SHAP[str(v)] for v in selected['variabel']]
batang = go.Figure(go.Bar(
    x=selected['shap_rata'], y=selected['variabel'].astype(str), orientation='h',
    marker_color=colors, error_x=dict(type='data', array=selected['shap_std']),
    customdata=selected[['kontribusi', 'jumlah_lag']].to_numpy(),
    hovertemplate='%{y}: %{x:.4f} °C<br>Kontribusi %{customdata[0]:.2f}%<br>%{customdata[1]} lag<extra></extra>'))
batang.update_layout(title=f'{pilihan}–RF: rata-rata ± simpangan baku',
                     xaxis_title='Rata-rata jumlah |SHAP| per variabel (°C)', height=360)
donat = go.Figure(go.Pie(labels=selected['variabel'].astype(str), values=selected['kontribusi'],
                        marker_colors=colors, hole=.55, sort=False, textinfo='label+percent'))
donat.update_layout(
    title=f'{pilihan}–RF: proporsi kontribusi', height=360,
    margin=dict(l=24, r=24, t=64, b=48),
    legend=dict(orientation="h", x=0.5, xanchor="center",
                y=-0.06, yanchor="top"),
)
left, right = st.columns(2)
left.plotly_chart(batang, width="stretch")
right.plotly_chart(donat, width="stretch")
st.caption("Sumber: tabel_vector_shap_summary.csv, dibuat oleh sel agregasi pada notebook lama. "
           "Garis menunjukkan simpangan baku, bukan interval kepercayaan.")

shap_klaster = data.muat_shap_klaster("M4: Lag LST + NDVI + NDBI (per Cluster)")
komposisi_klaster = shap_klaster.assign(
    label_klaster=lambda df: "Klaster " + df["klaster"].astype(str)
)
st.subheader("Porsi kontribusi tiap variabel per klaster")
st.plotly_chart(
    viz.komposisi(
        komposisi_klaster,
        "label_klaster",
        "variabel",
        "kontribusi",
        WARNA_SHAP,
        "Kontribusi LST, NDVI, dan NDBI per klaster — M4–RF",
        "Kontribusi terhadap prediksi (%)",
        "Klaster",
    ),
    width="stretch",
)
ui.keterangan(
    "Setiap batang menunjukkan komposisi kontribusi LST, NDVI, dan NDBI pada satu "
    "klaster dalam model <b>M4–RF</b>. Warna segmen membedakan variabel, sedangkan "
    "label di kiri menunjukkan nomor klaster. Persentase dihitung dari rata-rata "
    "besar SHAP tiap variabel di klaster tersebut; totalnya sekitar 100% karena "
    "pembulatan. Nilai ini menunjukkan besar kontribusi, bukan arah perubahan suhu."
)
st.caption("Sumber: true_vector_shap_cluster_M4_LagAll_byCluster.csv — hasil SHAP penelitian tersimpan.")

st.divider()
st.subheader("Hasil SHAP masing-masing klaster — M4–RF")
st.caption(
    "Lag LST + NDVI + NDBI, dengan model terpisah per klaster. "
    "Warna mengikuti nomor klaster pada peta. Semua grafik memakai skala yang sama."
)
batas_shap = float(shap_klaster["shap_rata"].max()) * 1.35
for awal in (1, 3):
    kolom_klaster = st.columns(2, gap="medium")
    for wadah, nomor in zip(kolom_klaster, (awal, awal + 1)):
        anggota = shap_klaster[shap_klaster["klaster"].eq(nomor)].copy()
        anggota = anggota.set_index("variabel").loc[["LST", "NDVI", "NDBI"]].reset_index()
        dominan = anggota.loc[anggota["shap_rata"].idxmax()]
        grafik = go.Figure(go.Bar(
            x=anggota["shap_rata"], y=anggota["variabel"].astype(str),
            orientation="h", marker_color=viz.WARNA_CLUSTER[nomor],
            text=[f"{nilai:.3f} °C" for nilai in anggota["shap_rata"]],
            textposition="outside", cliponaxis=False,
            customdata=anggota[["kontribusi", "shap_std", "n_grid"]].to_numpy(),
            hovertemplate=("%{y}<br>Rata-rata |SHAP|: %{x:.4f} °C"
                           "<br>Proporsi: %{customdata[0]:.2f}%"
                           "<br>Simpangan baku: %{customdata[1]:.4f} °C"
                           "<br>Sampel: %{customdata[2]:.0f} grid<extra></extra>"),
        ))
        grafik.update_layout(
            title=dict(text=f"Klaster {nomor} · {int(anggota['n_grid'].iloc[0])} sampel grid",
                       font=dict(size=15)),
            height=280, showlegend=False, margin=dict(l=58, r=24, t=55, b=48),
            xaxis=dict(title="Rata-rata jumlah |SHAP| (°C)", range=[0, batas_shap]),
            yaxis=dict(title=None, autorange="reversed"),
        )
        wadah.plotly_chart(grafik, width="stretch", config={"displayModeBar": False})
        wadah.caption(
            f"Kontribusi terbesar: {dominan['variabel']} ({dominan['kontribusi']:.2f}%). "
            + " · ".join(f"{row.variabel}: {row.kontribusi:.2f}%"
                         for row in anggota.itertuples() if row.variabel != dominan['variabel'])
        )
ui.keterangan(
    "Nilai yang lebih besar berarti variabel lebih berperan dalam prediksi pada klaster "
    "tersebut. Karena memakai nilai absolut SHAP, grafik ini <b>tidak menunjukkan "
    "arah pemanasan atau pendinginan</b>. Jumlah sampel adalah grid yang digunakan "
    "untuk ringkasan SHAP, bukan seluruh anggota klaster."
)
st.caption(
    "Sumber: true_vector_shap_cluster_M4_LagAll_byCluster.csv, hasil penelitian tersimpan; "
    "bukan SHAP yang dihitung ulang dari artefak model pada halaman Forecasting."
)
with st.expander("Tabel SHAP per klaster dan unduhan"):
    tabel_klaster = shap_klaster.rename(columns={
        "klaster": "Klaster", "variabel": "Variabel", "shap_rata": "Rata-rata (°C)",
        "shap_std": "Simpangan baku (°C)", "median": "Median (°C)",
        "kontribusi": "Proporsi (%)", "n_grid": "Sampel grid",
    })[["Klaster", "Variabel", "Rata-rata (°C)", "Simpangan baku (°C)",
        "Median (°C)", "Proporsi (%)", "Sampel grid"]]
    st.dataframe(tabel_klaster.style.format({
        "Rata-rata (°C)": "{:.4f}", "Simpangan baku (°C)": "{:.4f}",
        "Median (°C)": "{:.4f}", "Proporsi (%)": "{:.2f}",
    }), hide_index=True, width="stretch")
    st.download_button("Unduh SHAP per klaster", tabel_klaster.to_csv(index=False).encode("utf-8-sig"),
                       file_name="shap_m4_rf_per_klaster.csv", mime="text/csv")

st.subheader("Lag yang paling berpengaruh")
lag = ringkas[["kode", "variabel", "jumlah_lag", "lag_terkuat", "shap_lag_terkuat"]].rename(
    columns={
        "kode": "Model",
        "variabel": "Variabel",
        "jumlah_lag": "Jumlah lag",
        "lag_terkuat": "Lag terkuat",
        "shap_lag_terkuat": "SHAP lag terkuat (°C)",
    }
)
st.dataframe(
    lag.style.format({"SHAP lag terkuat (°C)": "{:.4f}", "Lag terkuat": "{:.0f}"}),
    hide_index=True,
    width="stretch",
)
ui.keterangan(
    "Pada seluruh konfigurasi, lag LST terkuat selalu jatuh pada <b>2012</b> dan lag NDBI "
    "terkuat selalu pada <b>2021</b>. Perlu dicatat bahwa 2012 adalah periode dengan jendela "
    "komposit terpanjang (Juni–Agustus) sekaligus rata-rata LST terendah kedua, sehingga "
    "kuatnya lag ini sebaiknya diperiksa ulang terhadap kemungkinan pengaruh perbedaan "
    "jendela komposit antarperiode, bukan semata pola iklim."
)

with st.expander("Tabel vector SHAP lengkap"):
    penuh = ringkas[
        ["model", "variabel", "jumlah_lag", "shap_rata", "shap_std", "kontribusi"]
    ].rename(
        columns={
            "model": "Konfigurasi",
            "variabel": "Variabel",
            "jumlah_lag": "Jumlah lag",
            "shap_rata": "Vector SHAP rata-rata (°C)",
            "shap_std": "Simpangan baku",
            "kontribusi": "Kontribusi (%)",
        }
    )
    st.dataframe(
        penuh.style.format(
            {
                "Vector SHAP rata-rata (°C)": "{:.5f}",
                "Simpangan baku": "{:.5f}",
                "Kontribusi (%)": "{:.2f}%",
            }
        ),
        hide_index=True,
        width="stretch",
    )

