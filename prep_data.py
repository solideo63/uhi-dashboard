"""Ekstrak hasil evaluasi dari 'Hasil Evaluasi Cluster.xlsx' menjadi CSV yang rapi.

Dijalankan sekali saja:  .venv\\Scripts\\python.exe prep_data.py
Hasilnya dipakai langsung oleh dashboard sehingga angka yang tampil adalah
hasil asli penelitian, bukan hasil pelatihan ulang.
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
XLSX = DATA / "Hasil Evaluasi Cluster.xlsx"


def evaluasi_cluster() -> pd.DataFrame:
    """Sheet 'evaluation_all_k (2)': metrik internal untuk k = 2..7 × 3 metode."""
    df = pd.read_excel(XLSX, sheet_name="evaluation_all_k (2)")
    df = df.rename(
        columns={
            "Method": "metode",
            "K": "k",
            "WCSS": "wcss",
            "Silhouette": "silhouette",
            "DB_Index": "db_index",
            "Dunn_Index": "dunn_index",
        }
    )
    return df.sort_values(["k", "metode"]).reset_index(drop=True)


def evaluasi_model() -> pd.DataFrame:
    """Sheet4 baris 1-8: 4 konfigurasi model × 2 algoritma (RF, SVR)."""
    df = pd.read_excel(XLSX, sheet_name="Sheet4", nrows=8)
    df = df.rename(
        columns={
            "Config": "konfigurasi",
            "Algorithm": "algoritma",
            "N_Features": "n_fitur",
            "Split": "split",
            "Train_R2": "train_r2",
            "Train_Adj_R2": "train_adj_r2",
            "Test_R2": "test_r2",
            "Test_Adj_R2": "test_adj_r2",
            "Test_RMSE": "test_rmse",
            "Test_MAE": "test_mae",
            "Test_MAPE": "test_mape",
            "CV_R2_Mean": "cv_r2_mean",
            "CV_R2_Std": "cv_r2_std",
        }
    )
    df = df[[c for c in df.columns if not c.startswith("Unnamed")]]
    # Kode model M1..M4 diambil dari awal string konfigurasi.
    df.insert(0, "model", df["konfigurasi"].str.split(":").str[0].str.strip())
    return df.reset_index(drop=True)


def definisi_model() -> pd.DataFrame:
    """Sheet3: deskripsi tiap konfigurasi model."""
    df = pd.read_excel(XLSX, sheet_name="Sheet3")
    df = df.rename(
        columns={
            "No": "no",
            "Kode Model": "kode",
            "Deskripsi Model": "deskripsi",
            "Variabel/Fitur": "fitur",
        }
    )
    # Excel menyimpan en-dash sebagai byte yang rusak saat diekspor; rapikan.
    for kolom in ("deskripsi", "fitur"):
        df[kolom] = df[kolom].astype(str).str.replace("�", "-", regex=False)
    return df


if __name__ == "__main__":
    for nama, frame in [
        ("evaluasi_cluster.csv", evaluasi_cluster()),
        ("evaluasi_model.csv", evaluasi_model()),
        ("definisi_model.csv", definisi_model()),
    ]:
        tujuan = DATA / nama
        frame.to_csv(tujuan, index=False, encoding="utf-8")
        print(f"tersimpan: {tujuan.name}  ({len(frame)} baris)")
