"""Halaman clustering: peta klaster, pola LST tiap klaster, dan evaluasi metode."""

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import uhi_data as data
import uhi_ui as ui
import uhi_viz as viz

ui.judul_halaman(
    "Pengelompokan pola",
    "Time Series Clustering",
    "Setiap grid diwakili oleh deret LST-nya sepanjang enam periode, lalu dikelompokkan "
    "menjadi empat klaster. Ketiga metode memakai ukuran kemiripan yang berbeda: "
    "<b>K-Means Euclidean</b> membandingkan nilai pada periode yang sama, "
    "<b>DTW K-Means</b> membolehkan pergeseran waktu, dan "
    "<b>k-Shape</b> membandingkan bentuk deret setelah normalisasi.",
)

metode = st.radio("Metode clustering", list(data.METODE_CLUSTER), horizontal=True)
kolom = data.METODE_CLUSTER[metode]

peta_data = data.muat_peta_panel()
panel = data.muat_panel()
grid_cluster = data.muat_cluster().dropna(subset=[kolom]).copy()
grid_cluster[kolom] = grid_cluster[kolom].astype(int)

# Geometri satu grid berulang di tiap tahun; ambil satu baris saja per grid.
peta_cluster = peta_data[peta_data["tahun"] == data.TAHUN[-1]].copy()
peta_cluster = peta_cluster[peta_cluster[kolom].notna()]

jumlah = grid_cluster[kolom].value_counts().sort_index()

profil = (
    panel.dropna(subset=[kolom, "lst"])
    .assign(**{kolom: lambda d: d[kolom].astype(int)})
    .groupby(["tahun", kolom])["lst"]
    .mean()
    .unstack()
)
profil.columns = [f"Klaster {int(c)}" for c in profil.columns]
profil = profil.reset_index()

ui.kartu(
    [
        ("Metode", metode, "k = 4"),
        ("Grid terklaster", f"{len(grid_cluster)}", "grid dengan deret LST lengkap"),
        ("Klaster terpanas", f"Klaster {int(profil.set_index('tahun').mean().idxmax().split()[-1])}",
         f"{profil.set_index('tahun').mean().max():.2f} °C rata-rata"),
        ("Klaster tersejuk", f"Klaster {int(profil.set_index('tahun').mean().idxmin().split()[-1])}",
         f"{profil.set_index('tahun').mean().min():.2f} °C rata-rata"),
    ]
)

st.divider()

kiri, kanan = st.columns([3, 2], gap="large")

with kiri:
    st.subheader(f"Sebaran spasial klaster — {metode}")
    st.markdown(viz.legenda_cluster(jumlah), unsafe_allow_html=True)
    st_folium(
        viz.peta_cluster(peta_cluster, kolom, metode),
        width=None,
        height=520,
        returned_objects=[],
        key=f"peta-cluster-{kolom}",
    )

with kanan:
    st.subheader("Pola LST tiap klaster")
    st.plotly_chart(
        viz.garis_tren(
            profil[profil["tahun"] <= 2021],
            "tahun",
            {nama: nama for nama in profil.columns if nama != "tahun"},
            f"Rata-rata LST per klaster — {metode}",
            "LST (°C)",
        ),
        width="stretch",
    )

st.subheader("Karakteristik tiap klaster")
gabung = panel.dropna(subset=[kolom]).assign(**{kolom: lambda d: d[kolom].astype(int)})
karakter = (
    gabung.groupby(kolom)
    .agg(
        Grid=("grid_id", "nunique"),
        LST=("lst", "mean"),
        LST_min=("lst", "min"),
        LST_maks=("lst", "max"),
        NDVI=("ndvi", "mean"),
        NDBI=("ndbi", "mean"),
    )
    .reset_index()
    .rename(
        columns={
            kolom: "Klaster",
            "LST": "LST rata-rata (°C)",
            "LST_min": "LST min (°C)",
            "LST_maks": "LST maks (°C)",
            "NDVI": "NDVI rata-rata",
            "NDBI": "NDBI rata-rata",
        }
    )
)
st.dataframe(
    karakter.style.format(
        {
            "LST rata-rata (°C)": "{:.2f}",
            "LST min (°C)": "{:.2f}",
            "LST maks (°C)": "{:.2f}",
            "NDVI rata-rata": "{:.4f}",
            "NDBI rata-rata": "{:.4f}",
        }
    ),
    hide_index=True,
    width="stretch",
)

st.divider()

st.subheader("Evaluasi metode clustering")
ui.keterangan(
    "Silhouette dan Dunn Index makin baik bila makin besar, sedangkan "
    "Davies–Bouldin Index makin baik bila makin kecil. WCSS digunakan untuk "
    "melihat titik siku pada elbow method ketika jumlah klaster bertambah. "
    "Angka berikut diambil dari berkas hasil evaluasi penelitian."
)

evaluasi = data.muat_evaluasi_cluster()
pada_k4 = evaluasi[evaluasi["k"] == 4].copy()

tabel_k4 = pada_k4.rename(
    columns={
        "metode": "Metode",
        "silhouette": "Silhouette ↑",
        "db_index": "Davies–Bouldin ↓",
        "dunn_index": "Dunn ↑",
        "wcss": "WCSS ↓",
    }
)[["Metode", "Silhouette ↑", "Davies–Bouldin ↓", "Dunn ↑", "WCSS ↓"]]

st.dataframe(
    tabel_k4.style.format(
        {"Silhouette ↑": "{:.4f}", "Davies–Bouldin ↓": "{:.4f}", "Dunn ↑": "{:.4f}", "WCSS ↓": "{:.2f}"}
    ).highlight_max(subset=["Silhouette ↑", "Dunn ↑"], color="#e4f2e2")
    .highlight_min(subset=["Davies–Bouldin ↓", "WCSS ↓"], color="#e4f2e2"),
    hide_index=True,
    width="stretch",
)

terbaik = pada_k4.loc[pada_k4["silhouette"].idxmax()]
menang = sum(
    [
        pada_k4["silhouette"].idxmax() == terbaik.name,
        pada_k4["db_index"].idxmin() == terbaik.name,
        pada_k4["dunn_index"].idxmax() == terbaik.name,
        pada_k4["wcss"].idxmin() == terbaik.name,
    ]
)
st.success(
    f"**Metode clustering terbaik pada k = 4: {terbaik['metode']}** — unggul pada {menang} dari 4 metrik "
    f"(Silhouette {terbaik['silhouette']:.4f}, Davies–Bouldin {terbaik['db_index']:.4f}, "
    f"Dunn {terbaik['dunn_index']:.4f}, WCSS {terbaik['wcss']:.2f})."
)

st.subheader("Perbandingan metrik pada berbagai jumlah klaster")
ui.keterangan(
    "Perbandingan k = 2 sampai k = 7 memperlihatkan apakah pilihan k = 4 sudah memadai. "
    "Garis putus vertikal menandai k = 4."
)

nama_metrik = {
    "silhouette": ("Silhouette ↑", "Silhouette"),
    "db_index": ("Davies–Bouldin ↓", "DB Index"),
    "dunn_index": ("Dunn ↑", "Dunn Index"),
}


def grafik_evaluasi(kunci, judul, sumbu):
    lebar = evaluasi.pivot(index="k", columns="metode", values=kunci).reset_index()
    urutan = ["K-Means", "DTW K-Means", "K-Shape"]
    fig = viz.garis_tren(lebar, "k", {n: n for n in urutan}, judul, sumbu)
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=52, r=88, t=56, b=52),
        title=dict(text=judul, font=dict(size=15), x=0.02),
    )
    # Kolom label di luar area data menjaga nama metode tetap sejajar dan
    # memberi ruang yang sama pada ketiga grafik tanpa legenda berulang.
    for annotation in fig.layout.annotations:
        nama = annotation.text.strip()
        annotation.update(
            x=1.03, xref="paper", xanchor="left", yanchor="middle",
            text=nama.replace("DTW K-Means", "DTW<br>K-Means"),
            align="left", font=dict(size=11, color=viz.TINTA_SEKUNDER),
        )
    fig.update_xaxes(title="Jumlah klaster (k)", range=[1.8, 7.25],
                     title_font_size=12, tickfont_size=11)
    fig.update_yaxes(title_font_size=12, tickfont_size=11)
    fig.add_vline(x=4, line_width=2, line_dash="dash", line_color=viz.SUMBU)
    return fig


st.plotly_chart(
    grafik_evaluasi("wcss", "WCSS — Elbow Method", "WCSS"),
    width="stretch", config={"displayModeBar": False},
)
ui.keterangan(
    "<b>Elbow method: cari titik yang membentuk siku.</b> WCSS mengukur jumlah "
    "kuadrat jarak anggota klaster terhadap pusat klasternya. Saat jumlah klaster "
    "(k) bertambah, WCSS biasanya menurun. Titik elbow terlihat ketika kurva "
    "berubah dari penurunan tajam menjadi lebih landai, sehingga menyerupai "
    "<b>sudut siku</b>; bentuknya tidak harus tepat 90°. Setelah titik ini, "
    "penambahan klaster hanya memberi penurunan WCSS yang relatif kecil. "
    "Karena itu, pilih k di sekitar tekukan tersebut, bukan sekadar WCSS terkecil. "
    "Garis putus-putus pada k = 4 menandai pilihan penelitian, bukan penetapan "
    "titik elbow secara otomatis. Periksa juga tiga metrik di bawah untuk "
    "menilai kualitas pemisahan klaster."
)

kolom_grafik = st.columns(3, gap="medium")
for kolom_metrik, (kunci, (judul, sumbu)) in zip(kolom_grafik, nama_metrik.items()):
    kolom_metrik.plotly_chart(grafik_evaluasi(kunci, judul, sumbu), width="stretch",
                            config={"displayModeBar": False})

with st.expander("Tabel evaluasi lengkap k = 2 sampai 7"):
    lengkap = evaluasi.rename(
        columns={
            "metode": "Metode",
            "k": "k",
            "wcss": "WCSS",
            "silhouette": "Silhouette",
            "db_index": "Davies–Bouldin",
            "dunn_index": "Dunn",
        }
    )
    st.dataframe(lengkap, hide_index=True, width="stretch")

with st.expander("Perbandingan label antarmetode"):
    ui.keterangan(
        "Nomor klaster tidak sebanding antarmetode; tabel silang berikut menunjukkan "
        "berapa banyak grid yang dikelompokkan bersama oleh dua metode berbeda."
    )
    lain = st.selectbox(
        "Bandingkan dengan",
        [m for m in data.METODE_CLUSTER if m != metode],
    )
    kolom_lain = data.METODE_CLUSTER[lain]
    pasangan = data.muat_cluster().dropna(subset=[kolom, kolom_lain])
    silang = pd.crosstab(
        pasangan[kolom].astype(int), pasangan[kolom_lain].astype(int)
    )
    silang.index = [f"{metode} — klaster {i}" for i in silang.index]
    silang.columns = [f"{lain} — klaster {c}" for c in silang.columns]
    st.dataframe(silang, width="stretch")
