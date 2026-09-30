"""Reproduksi model regresi Random Forest dan Support Vector Regression.

Rancangan model mengikuti skema penelitian: LST tahun terakhir (2024) diduga
dari lag LST lima periode sebelumnya (2009-2021), dengan atau tanpa tambahan
NDVI dan NDBI, dan dilatih atas seluruh grid atau terpisah per klaster.

Angka evaluasi resmi penelitian dibaca dari ``data/evaluasi_model.csv``. Model
di sini dilatih ulang saat aplikasi berjalan agar dashboard dapat menampilkan
sebaran prediksi per grid dan proyeksi ke depan, yang tidak tersimpan di berkas
hasil. Karena penyetelan hiperparameter tidak ikut tercatat, angkanya dapat
sedikit berbeda dari tabel resmi dan ditampilkan terpisah.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

import uhi_data

TAHUN_LAG = [2009, 2012, 2015, 2018, 2021]
TAHUN_TARGET = 2024
LANGKAH = 3  # jarak antarperiode dalam tahun

ALGORITMA = ["Random Forest", "Support Vector Regression"]


def _buat_model(algoritma: str):
    if algoritma == "Random Forest":
        return RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    return make_pipeline(StandardScaler(), SVR(kernel="rbf", C=10.0, gamma="scale", epsilon=0.1))


@dataclass
class Hasil:
    """Hasil satu kali pelatihan: metrik ringkas dan prediksi per grid uji."""

    metrik: dict[str, float]
    prediksi: pd.DataFrame  # grid_id, cluster, aktual, prediksi
    n_fitur: int


def _metrik(y_asli: np.ndarray, y_duga: np.ndarray, n_fitur: int) -> dict[str, float]:
    n = len(y_asli)
    r2 = r2_score(y_asli, y_duga)
    # R kuadrat terkoreksi hanya bermakna bila derajat bebas masih tersisa.
    penyebut = n - n_fitur - 1
    adj = 1 - (1 - r2) * (n - 1) / penyebut if penyebut > 0 else float("nan")
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_asli, y_duga))),
        "MAE": float(mean_absolute_error(y_asli, y_duga)),
        "MAPE": float(np.mean(np.abs((y_asli - y_duga) / y_asli))),
        "R2": float(r2),
        "Adj_R2": float(adj),
    }


def metrik(aktual, prediksi, n_fitur: int) -> dict[str, float]:
    """Metrik regresi (RMSE, MAE, MAPE, R2, Adj_R2) untuk sepasang deret.

    Dipakai halaman peramalan untuk menghitung ulang metrik dari prediksi
    per grid yang dibaca dari berkas hasil penelitian.
    """
    return _metrik(np.asarray(aktual, dtype=float), np.asarray(prediksi, dtype=float), n_fitur)


@st.cache_data(show_spinner=False)
def _bahan() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Matriks fitur penuh, target, dan label klaster K-Means, sejajar per grid."""
    lst = uhi_data.matriks_lst()
    ndvi, ndbi = uhi_data.matriks_indeks()
    cluster = uhi_data.muat_cluster().set_index("grid_id")

    grid = lst.index.intersection(ndvi.index).intersection(cluster.index)
    lst, ndvi, ndbi, cluster = lst.loc[grid], ndvi.loc[grid], ndbi.loc[grid], cluster.loc[grid]

    fitur = pd.DataFrame(index=grid)
    for tahun in TAHUN_LAG:
        fitur[f"lst_{tahun}"] = lst[tahun]
    for tahun in uhi_data.TAHUN:
        fitur[f"ndvi_{tahun}"] = ndvi[tahun]
        fitur[f"ndbi_{tahun}"] = ndbi[tahun]

    return fitur, lst[TAHUN_TARGET], cluster["k-means_cluster"]


@st.cache_data(show_spinner="Melatih model ...")
def latih(algoritma: str, pakai_indeks: bool, per_cluster: bool) -> Hasil:
    """Latih dan evaluasi satu konfigurasi model.

    ``pakai_indeks`` menambahkan 12 kolom NDVI dan NDBI ke 5 kolom lag LST
    (total 17 fitur). ``per_cluster`` melatih satu model terpisah untuk tiap
    klaster K-Means, lalu menggabungkan prediksinya untuk dihitung metriknya.
    """
    fitur, target, cluster = _bahan()
    kolom = [k for k in fitur.columns if pakai_indeks or k.startswith("lst_")]
    X, y = fitur[kolom], target

    # Pembagian grid dilakukan sekali dan sama untuk semua konfigurasi, agar
    # perbandingan antarkonfigurasi adil.
    latih_arr, uji_arr = train_test_split(
        X.index.to_numpy(), test_size=0.2, random_state=42, stratify=cluster
    )
    grid_latih, grid_uji = pd.Index(latih_arr), pd.Index(uji_arr)

    duga = pd.Series(index=grid_uji, dtype=float)

    if per_cluster:
        for label in sorted(cluster.unique()):
            anggota = cluster[cluster == label].index
            latih_ini = grid_latih.intersection(anggota)
            uji_ini = grid_uji.intersection(anggota)
            if latih_ini.empty or uji_ini.empty:
                continue
            model = _buat_model(algoritma)
            model.fit(X.loc[latih_ini], y.loc[latih_ini])
            duga.loc[uji_ini] = model.predict(X.loc[uji_ini])
    else:
        model = _buat_model(algoritma)
        model.fit(X.loc[grid_latih], y.loc[grid_latih])
        duga.loc[grid_uji] = model.predict(X.loc[grid_uji])

    duga = duga.dropna()
    prediksi = pd.DataFrame(
        {
            "grid_id": duga.index,
            "cluster": cluster.loc[duga.index].values,
            "aktual": y.loc[duga.index].values,
            "prediksi": duga.values,
        }
    ).reset_index(drop=True)

    return Hasil(
        metrik=_metrik(prediksi["aktual"].to_numpy(), prediksi["prediksi"].to_numpy(), len(kolom)),
        prediksi=prediksi,
        n_fitur=len(kolom),
    )


@st.cache_data(show_spinner="Menghitung proyeksi ...")
def ramalkan(algoritma: str, per_cluster: bool, jumlah_langkah: int = 2) -> pd.DataFrame:
    """Proyeksikan LST ke periode berikutnya secara rekursif.

    Peramalan hanya memakai lag LST sebagai fitur. Dengan begitu jendela lag
    dapat digeser maju satu periode setiap langkah tanpa memerlukan NDVI dan
    NDBI masa depan yang memang belum tersedia. Hasilnya adalah proyeksi
    bersyarat: pola hubungan antarperiode dianggap tetap berlaku ke depan.
    """
    fitur, target, cluster = _bahan()
    kolom = [f"lst_{t}" for t in TAHUN_LAG]

    # Deret lengkap 2009-2024 per grid sebagai titik awal penggeseran jendela.
    deret = fitur[kolom].copy()
    deret[f"lst_{TAHUN_TARGET}"] = target

    def satu_model(X_latih, y_latih):
        model = _buat_model(algoritma)
        model.fit(X_latih, y_latih)
        return model

    if per_cluster:
        model_per_label = {
            label: satu_model(fitur.loc[cluster == label, kolom], target[cluster == label])
            for label in sorted(cluster.unique())
        }
    else:
        model_tunggal = satu_model(fitur[kolom], target)

    baris = []
    tahun_terakhir = TAHUN_TARGET
    for _ in range(jumlah_langkah):
        tahun_baru = tahun_terakhir + LANGKAH
        # Jendela lag bergeser: lima periode terakhir yang tersedia.
        jendela = deret.iloc[:, -5:]
        masukan = jendela.copy()
        masukan.columns = kolom

        hasil = pd.Series(index=deret.index, dtype=float)
        if per_cluster:
            for label, model in model_per_label.items():
                anggota = cluster[cluster == label].index
                hasil.loc[anggota] = model.predict(masukan.loc[anggota])
        else:
            hasil.iloc[:] = model_tunggal.predict(masukan)

        deret[f"lst_{tahun_baru}"] = hasil
        baris.append(pd.DataFrame({"grid_id": deret.index, "tahun": tahun_baru, "lst": hasil.values}))
        tahun_terakhir = tahun_baru

    ramalan = pd.concat(baris, ignore_index=True)
    ramalan["cluster"] = cluster.reindex(ramalan["grid_id"]).values
    return ramalan
