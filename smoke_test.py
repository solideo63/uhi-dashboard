"""Pemeriksaan cepat seluruh modul di luar Streamlit sebelum aplikasi dijalankan."""

import warnings

warnings.filterwarnings("ignore")

import pandas as pd

import uhi_data as data
import uhi_model as model
import uhi_viz as viz

print("grid          :", data.muat_grid().shape)
print("lst           :", data.muat_lst().shape)
print("indeks        :", data.muat_indeks().shape)
print("cluster       :", data.muat_cluster().shape)
print("panel         :", data.muat_panel().shape)
print("peta_panel    :", data.muat_peta_panel().shape)
print("matriks_lst   :", data.matriks_lst().shape)
ndvi, ndbi = data.matriks_indeks()
print("matriks ndvi  :", ndvi.shape, "sisa NaN:", int(ndvi.isna().sum().sum()))
print("evaluasi clust:", data.muat_evaluasi_cluster().shape)
print("evaluasi model:", data.muat_evaluasi_model().shape)

panel = data.muat_panel()
peta = data.muat_peta_panel()
potongan = peta[peta["tahun"] == 2024]

print("\n-- peta --")
viz.peta_kontinu(potongan, "lst", "LST", viz.RAMPA["lst"], " (°C)")
viz.peta_cluster(potongan[potongan["k-means_cluster"].notna()], "k-means_cluster", "K-Means")
print("peta kontinu & klaster: ok")

print("\n-- grafik --")
ringkas = panel.groupby("tahun")[["lst", "ndvi", "ndbi"]].mean().reset_index()
viz.garis_tren(ringkas, "tahun", {"LST": "lst"}, "x", "y")
viz.histogram(potongan["lst"], "x", "y", viz.RAMPA["lst"][2])
viz.batang_perbandingan(ringkas.head(3), "tahun", "lst", "x", "y", viz.RAMPA["lst"][2])
print("garis, histogram, batang: ok")

print("\n-- model --")
baris = []
for algoritma in model.ALGORITMA:
    for pakai_indeks in (False, True):
        for per_cluster in (False, True):
            hasil = model.latih(algoritma, pakai_indeks, per_cluster)
            baris.append(
                {
                    "algoritma": algoritma,
                    "fitur": hasil.n_fitur,
                    "per_cluster": per_cluster,
                    **{k: round(v, 4) for k, v in hasil.metrik.items()},
                }
            )
print(pd.DataFrame(baris).to_string(index=False))

print("\n-- proyeksi --")
ramalan = model.ramalkan("Random Forest", True, 2)
print(ramalan.groupby(["tahun", "cluster"])["lst"].mean().unstack().round(2).to_string())

riwayat = (
    panel.dropna(subset=["lst", "k-means_cluster"])
    .assign(cluster=lambda d: d["k-means_cluster"].astype(int))
    .groupby(["tahun", "cluster"])["lst"]
    .mean()
    .reset_index()
)
proyeksi = ramalan.groupby(["tahun", "cluster"])["lst"].mean().reset_index()
viz.garis_forecast(riwayat, proyeksi, "cluster", "x")
hasil = model.latih("Random Forest", True, True)
viz.sebar_prediksi(hasil.prediksi["aktual"], hasil.prediksi["prediksi"], "x", viz.RAMPA["lst"][2])
print("grafik forecast & sebar: ok")

print("\nSEMUA PEMERIKSAAN LOLOS")
