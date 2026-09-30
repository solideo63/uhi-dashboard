"""Halaman tren: perkembangan rata-rata LST, NDVI, dan NDBI antarperiode."""

import pandas as pd
import streamlit as st

import uhi_data as data
import uhi_ui as ui
import uhi_viz as viz

ui.judul_halaman(
    "Tren antarperiode",
    "Analisis Perubahan Temporal",
    "Setiap variabel dirata-ratakan atas seluruh grid pada tiap periode. "
    "Karena satuannya berbeda, LST, NDVI, dan NDBI ditampilkan pada grafik terpisah "
    "agar besaran perubahannya tidak menyesatkan bila dibandingkan langsung.",
)

panel = data.muat_panel()
ringkas = panel.groupby("tahun")[["lst", "ndvi", "ndbi"]].mean().reset_index()

matriks = data.matriks_lst()
awal, akhir = data.TAHUN[0], data.TAHUN[-1]
selisih = matriks[akhir].mean() - matriks[awal].mean()

ui.kartu(
    [
        (f"Rata-rata LST {awal}", f"{matriks[awal].mean():.2f} °C", "titik awal pengamatan"),
        (f"Rata-rata LST {akhir}", f"{matriks[akhir].mean():.2f} °C", "titik akhir pengamatan"),
        ("Perubahan LST", f"{selisih:+.2f} °C", f"selama {akhir - awal} tahun"),
        ("Periode terpanas", f"{matriks.mean().idxmax()}", f"{matriks.mean().max():.2f} °C rata-rata"),
    ]
)

st.divider()

st.subheader("Rata-rata LST antarperiode")
st.plotly_chart(
    viz.garis_tren(
        ringkas, "tahun", {"LST": "lst"}, "Rata-rata LST DKI Jakarta pada puncak kemarau", "LST (°C)"
    ),
    width="stretch",
)

sensor = data.sensor_per_tahun()
# Pergantian satelit terjadi di antara dua periode, sehingga penandanya
# diletakkan di tengah-tengah keduanya.
batas_sensor = [
    ((data.TAHUN[i] + data.TAHUN[i + 1]) / 2, sensor[data.TAHUN[i + 1]])
    for i in range(len(data.TAHUN) - 1)
    if sensor.get(data.TAHUN[i]) != sensor.get(data.TAHUN[i + 1])
]
peralihan = [
    f"{data.TAHUN[i]} → {data.TAHUN[i + 1]}"
    for i in range(len(data.TAHUN) - 1)
    if sensor.get(data.TAHUN[i]) != sensor.get(data.TAHUN[i + 1])
]


def tandai_sensor(fig):
    """Beri garis penanda pada tiap titik pergantian satelit."""
    for posisi, nama in batas_sensor:
        fig.add_vline(
            x=posisi,
            line_width=1.5,
            line_dash="dot",
            line_color=viz.SUMBU,
            annotation_text=f"→ {nama}",
            annotation_position="top",
            annotation_font=dict(size=10.5, color=viz.TINTA_REDUP),
        )
    return fig


# NDVI dan NDBI ragam nilainya kecil; sumbu-y kedua grafik disamakan lebarnya
# lewat rentang_minimum agar lonjakan di titik pergantian satelit tidak
# terbaca lebih dramatis daripada besarnya yang sebenarnya.
RENTANG_INDEKS = 0.2
kiri, kanan = st.columns(2, gap="large")
with kiri:
    st.subheader("Rata-rata NDVI")
    st.plotly_chart(
        tandai_sensor(
            viz.garis_tren(
                ringkas, "tahun", {"NDVI": "ndvi"}, "Rata-rata NDVI", "NDVI", RENTANG_INDEKS
            )
        ),
        width="stretch",
    )
with kanan:
    st.subheader("Rata-rata NDBI")
    st.plotly_chart(
        tandai_sensor(
            viz.garis_tren(
                ringkas, "tahun", {"NDBI": "ndbi"}, "Rata-rata NDBI", "NDBI", RENTANG_INDEKS
            )
        ),
        width="stretch",
    )

def _lompatan(kolom: str) -> tuple[float, float]:
    """Bandingkan lompatan terbesar di titik pergantian satelit dengan
    perubahan terbesar yang terjadi di dalam satu satelit yang sama."""
    nilai = ringkas.set_index("tahun")[kolom]
    antar, dalam = [], []
    for i in range(len(data.TAHUN) - 1):
        awal, akhir = data.TAHUN[i], data.TAHUN[i + 1]
        selisih = abs(nilai[akhir] - nilai[awal])
        (antar if sensor[awal] != sensor[akhir] else dalam).append(selisih)
    return max(antar), max(dalam)


ndvi_antar, ndvi_dalam = _lompatan("ndvi")
ndbi_antar, ndbi_dalam = _lompatan("ndbi")

ui.keterangan(
    "Satelit sumber NDVI dan NDBI berganti antarperiode: "
    + ", ".join(f"<b>{t}</b> {s}" for t, s in sensor.items())
    + ". Garis putus-putus pada kedua grafik menandai peralihan "
    + " dan ".join(peralihan)
    + ". <b>Kedua lonjakan terbesar jatuh tepat pada titik peralihan itu.</b> Pada NDVI, "
    f"perubahan terbesar antarsatelit mencapai {ndvi_antar:.3f}, sedangkan perubahan terbesar "
    f"di dalam satelit yang sama hanya {ndvi_dalam:.3f}. Pada NDBI selisihnya lebih tajam lagi: "
    f"{ndbi_antar:.3f} berbanding {ndbi_dalam:.3f} — nilainya praktis mendatar sepanjang tiga "
    "periode Landsat, lalu melompat begitu beralih ke Sentinel-2 dan mendatar lagi. "
    "Pola bertingkat seperti ini adalah ciri khas artefak perbedaan sensor, bukan pertumbuhan "
    "lahan terbangun yang sebenarnya. Sebelum tren NDVI dan NDBI dipakai sebagai temuan, "
    "nilainya perlu diselaraskan antarsensor terlebih dahulu.",
    samping=True,
)

st.divider()

st.subheader("Perubahan antarperiode")

perubahan = ringkas.copy()
for kolom in ("lst", "ndvi", "ndbi"):
    perubahan[f"Δ {kolom.upper()}"] = perubahan[kolom].diff()

tabel = perubahan.rename(
    columns={"tahun": "Tahun", "lst": "LST (°C)", "ndvi": "NDVI", "ndbi": "NDBI"}
)[["Tahun", "LST (°C)", "Δ LST", "NDVI", "Δ NDVI", "NDBI", "Δ NDBI"]]

st.dataframe(
    tabel.style.format(
        {
            "LST (°C)": "{:.2f}",
            "Δ LST": "{:+.2f}",
            "NDVI": "{:.4f}",
            "Δ NDVI": "{:+.4f}",
            "NDBI": "{:.4f}",
            "Δ NDBI": "{:+.4f}",
        },
        na_rep="—",
    ),
    hide_index=True,
    width="stretch",
)

st.subheader("Perubahan LST tiap langkah periode")
langkah = perubahan.dropna(subset=["Δ LST"]).copy()
langkah["label"] = [
    f"{data.TAHUN[i]}→{data.TAHUN[i + 1]}" for i in range(len(data.TAHUN) - 1)
]
st.plotly_chart(
    viz.batang_perbandingan(
        langkah, "label", "Δ LST", "Selisih rata-rata LST antarperiode", "Δ LST (°C)", viz.RAMPA["lst"][2]
    ),
    width="stretch",
)

st.divider()

st.subheader("Hubungan LST dengan NDVI dan NDBI")
korelasi = (
    panel.dropna(subset=["lst", "ndvi", "ndbi"])
    .groupby("tahun")
    .apply(
        lambda g: pd.Series(
            {"NDVI vs LST": g["lst"].corr(g["ndvi"]), "NDBI vs LST": g["lst"].corr(g["ndbi"])}
        ),
        include_groups=False,
    )
    .reset_index()
)
st.plotly_chart(
    tandai_sensor(
        viz.garis_tren(
            korelasi,
            "tahun",
            {"NDVI vs LST": "NDVI vs LST", "NDBI vs LST": "NDBI vs LST"},
            "Korelasi Pearson antarsel pada tiap periode",
            "Koefisien korelasi",
        )
    ),
    width="stretch",
)
ui.keterangan(
    "Korelasi dihitung antarsel dalam satu periode, bukan antarwaktu. "
    "Nilai negatif pada NDVI menunjukkan sel yang lebih bervegetasi cenderung lebih sejuk, "
    "sedangkan nilai positif pada NDBI menunjukkan sel yang lebih terbangun cenderung lebih panas."
)
