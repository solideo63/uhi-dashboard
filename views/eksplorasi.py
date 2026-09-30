"""Halaman eksplorasi: peta satu variabel pada satu tahun, plus statistiknya."""

import streamlit as st
from streamlit_folium import st_folium

import uhi_data as data
import uhi_ui as ui
import uhi_viz as viz

ui.judul_halaman(
    "Sebaran spasial",
    "Eksplorasi Spasio-Temporal",
    "Pilih periode dan variabel untuk melihat sebarannya pada grid 1 × 1 km. "
    "Arahkan kursor ke sebuah sel untuk membaca nilainya.",
)

pilih_tahun, pilih_variabel, _ = st.columns([1, 1, 2], gap="medium")
tahun = pilih_tahun.selectbox("Tahun", data.TAHUN, index=len(data.TAHUN) - 1)
variabel = pilih_variabel.radio("Variabel", list(data.VARIABEL), horizontal=True)

kolom, nama_panjang = data.VARIABEL[variabel]
satuan = " (°C)" if kolom == "lst" else ""

peta_data = data.muat_peta_panel()
potongan = peta_data[peta_data["tahun"] == tahun].copy()

if potongan[kolom].notna().sum() == 0:
    st.warning(
        f"**Tidak ada nilai {variabel} untuk periode {tahun}** pada berkas sumber. "
        "Pilih periode atau variabel lain."
    )
    st.stop()

stat = data.statistik(potongan[kolom])
format_nilai = (lambda v: f"{v:.2f} °C") if kolom == "lst" else (lambda v: f"{v:.4f}")

ui.kartu(
    [
        ("Minimum", format_nilai(stat["min"]), f"{variabel} terendah"),
        ("Maksimum", format_nilai(stat["maks"]), f"{variabel} tertinggi"),
        ("Rata-rata", format_nilai(stat["rata"]), f"median {format_nilai(stat['median'])}"),
        ("Simpangan baku", format_nilai(stat["std"]), "sebaran antarsel"),
        ("Grid terisi", f"{stat['n']}", f"dari {len(potongan)} grid"),
    ]
)

if stat["n"] < len(potongan):
    st.caption(
        f"**{len(potongan) - stat['n']} grid** tidak memiliki nilai {variabel} pada periode "
        f"{tahun} dan digambar berwarna abu-abu pada peta."
    )

peta, samping = st.columns([3, 2], gap="large")

with peta:
    st.subheader(f"{nama_panjang} — {tahun}")
    st.markdown(
        viz.legenda_kontinu(
            potongan[kolom],
            viz.RAMPA[kolom],
            variabel,
            satuan,
            desimal=2 if kolom == "lst" else 3,
        ),
        unsafe_allow_html=True,
    )
    st_folium(
        viz.peta_kontinu(potongan, kolom, variabel, viz.RAMPA[kolom], satuan),
        width=None,
        height=520,
        returned_objects=[],
        key=f"peta-{kolom}-{tahun}",
    )

with samping:
    st.subheader("Distribusi antarsel")
    st.plotly_chart(
        viz.histogram(
            potongan[kolom],
            f"Sebaran {variabel} pada {tahun}",
            f"{variabel}{satuan}",
            viz.RAMPA[kolom][2],
        ),
        width="stretch",
    )

    with st.expander("Lihat data grid"):
        tabel = (
            potongan[["wilayah", "grid_id", kolom]]
            .dropna(subset=[kolom])
            .sort_values(kolom, ascending=False)
            .rename(
                columns={"wilayah": "Kecamatan", "grid_id": "Grid", kolom: f"{variabel}{satuan}"}
            )
        )
        st.dataframe(tabel, hide_index=True, width="stretch", height=320)
        st.download_button(
            "Unduh CSV",
            tabel.to_csv(index=False).encode("utf-8"),
            file_name=f"{kolom}_{tahun}.csv",
            mime="text/csv",
        )

sensor = data.sensor_per_tahun().get(tahun, "—")
if kolom == "lst":
    st.caption(
        f"Komposit citra periode {tahun} diambil pada bulan {data.JENDELA_BULAN[tahun]}, "
        "menyesuaikan ketersediaan citra bebas awan pada puncak musim kemarau tiap tahun."
    )
else:
    rata_citra = potongan["n_citra"].mean()
    st.caption(
        f"NDVI dan NDBI periode {tahun} disusun dari citra **{sensor}**, rata-rata "
        f"{rata_citra:.1f} citra per sel. Satelit yang dipakai berganti antarperiode "
        "(Landsat 7 → Landsat 8 → Sentinel-2), sehingga perbandingan antarperiode "
        "perlu memperhitungkan perbedaan karakteristik sensornya."
    )
