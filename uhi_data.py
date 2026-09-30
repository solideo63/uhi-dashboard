"""Pemuatan dan penggabungan data UHI-LST DKI Jakarta.

Tiga berkas GeoJSON hasil ekspor Google Earth Engine dipakai bersama:

* ``LSTPuncakKemarau.geojson``                        - LST puncak kemarau,
    format panjang (644 grid x 6 periode), kolom ``mean``.
* ``FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson`` - NDVI & NDBI, format
    panjang dengan kolom ``year``, ``NDVI``, dan ``NDBI``.
* ``cluster_spatial_k4.geojson``                      - label klaster k=4 untuk
    tiga metode.

Geometri grid diambil dari berkas NDVI/NDBI karena di sanalah seluruh 644
``grid_id`` hadir lengkap.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"

BERKAS_INDEKS = DATA / "FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson"

TAHUN = [2009, 2012, 2015, 2018, 2021, 2024]

# Jendela bulan puncak kemarau yang dipakai saat komposit citra tiap periode.
JENDELA_BULAN = {
    2009: "Agustus",
    2012: "Juni - Agustus",
    2015: "Agustus - September",
    2018: "Agustus - September",
    2021: "Agustus",
    2024: "Juli - Agustus",
}

METODE_CLUSTER = {
    "K-Means Euclidean": "k-means_cluster",
    "DTW K-Means": "dtw_k-means_cluster",
    "k-Shape": "k-shape_cluster",
}

# Nama metode sebagaimana tertulis pada berkas evaluasi Excel.
METODE_EVALUASI = {
    "K-Means Euclidean": "K-Means",
    "DTW K-Means": "DTW K-Means",
    "k-Shape": "K-Shape",
}

VARIABEL = {
    "LST": ("lst", "Suhu Permukaan Daratan (°C)"),
    "NDVI": ("ndvi", "Indeks Vegetasi"),
    "NDBI": ("ndbi", "Indeks Lahan Terbangun"),
}


@st.cache_data(show_spinner="Memuat geometri grid 1 x 1 km ...")
def muat_grid() -> gpd.GeoDataFrame:
    """Geometri 644 grid 1 x 1 km beserta titik pusatnya.

    Berkas indeks berformat panjang sehingga tiap grid muncul sekali per
    tahun; yang diambil cukup satu barisnya karena geometrinya sama.
    """
    gdf = gpd.read_file(BERKAS_INDEKS).drop_duplicates("grid_id")[["grid_id", "geometry"]]
    gdf = gdf.set_crs("EPSG:4326", allow_override=True).reset_index(drop=True)
    # Sentroid dihitung pada CRS metrik agar tidak bias, lalu dikembalikan ke lon/lat.
    pusat = gdf.to_crs("EPSG:3857").geometry.centroid.to_crs("EPSG:4326")
    gdf["lon"] = pusat.x
    gdf["lat"] = pusat.y
    return gdf


@st.cache_data(show_spinner="Memuat data LST ...")
def muat_lst() -> pd.DataFrame:
    """LST per grid per tahun dalam format panjang."""
    gdf = gpd.read_file(DATA / "LSTPuncakKemarau.geojson")
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    df = df.rename(columns={"period": "tahun", "mean": "lst"})
    return df[["grid_id", "tahun", "lst"]].sort_values(["grid_id", "tahun"]).reset_index(drop=True)


@st.cache_data(show_spinner="Memuat data NDVI & NDBI ...")
def muat_indeks() -> pd.DataFrame:
    """NDVI dan NDBI per grid per tahun, beserta keterangan penyusunannya.

    Berkas sumber sudah berformat panjang. Kolom ``sensor`` menyebut satelit
    asal komposit dan ``n_citra`` menyebut banyaknya citra yang dipakai untuk
    menyusunnya; keduanya dipertahankan karena menentukan seberapa kuat sebuah
    nilai dapat dipercaya. Nilai yang kosong dibiarkan apa adanya; pengisiannya
    hanya dilakukan di :func:`matriks_indeks` untuk keperluan pemodelan.
    """
    gdf = gpd.read_file(BERKAS_INDEKS)
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    df = df.rename(
        columns={"year": "tahun", "NDVI": "ndvi", "NDBI": "ndbi", "count": "n_citra"}
    )
    # Tahun tersimpan sebagai teks pada berkas sumber.
    df["tahun"] = df["tahun"].astype(int)
    kolom = ["grid_id", "tahun", "ndvi", "ndbi", "sensor", "n_citra"]
    return df[kolom].sort_values(["grid_id", "tahun"]).reset_index(drop=True)


@st.cache_data
def sensor_per_tahun() -> dict[int, str]:
    """Satelit asal komposit tiap periode, dibaca dari data agar selalu benar."""
    nama = {"landsat7": "Landsat 7", "landsat8": "Landsat 8", "sentinel2": "Sentinel-2"}
    utama = muat_indeks().groupby("tahun")["sensor"].agg(lambda s: s.mode().iloc[0])
    return {int(t): nama.get(v, str(v)) for t, v in utama.items()}


@st.cache_data(show_spinner="Memuat label klaster ...")
def muat_cluster() -> pd.DataFrame:
    """Label klaster k=4 untuk ketiga metode time series clustering."""
    gdf = gpd.read_file(DATA / "cluster_spatial_k4.geojson")
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    return df[["grid_id", *METODE_CLUSTER.values()]].reset_index(drop=True)


@st.cache_data(show_spinner="Menggabungkan panel data ...")
def muat_panel() -> pd.DataFrame:
    """Panel grid x tahun berisi LST, NDVI, NDBI, dan label klaster.

    Nilai yang kosong pada sumber tetap dibiarkan ``NaN`` supaya halaman
    eksplorasi menampilkan cakupan data apa adanya.
    """
    panel = muat_lst().merge(muat_indeks(), on=["grid_id", "tahun"], how="outer")
    panel = panel.merge(muat_cluster(), on="grid_id", how="left")
    return panel.sort_values(["grid_id", "tahun"]).reset_index(drop=True)


@st.cache_data
def muat_peta_panel() -> gpd.GeoDataFrame:
    """Panel data yang sudah disatukan dengan geometri dan nama wilayah grid."""
    gabung = muat_grid().merge(muat_panel(), on="grid_id", how="right")
    gabung = gabung.merge(wilayah_grid(), on="grid_id", how="left")
    return gpd.GeoDataFrame(gabung, geometry="geometry", crs="EPSG:4326")


@st.cache_data
def matriks_lst() -> pd.DataFrame:
    """Matriks deret waktu LST: satu baris per grid, satu kolom per tahun.

    Grid yang tidak memiliki nilai LST lengkap dibuang karena tidak dapat
    dipakai baik untuk clustering maupun untuk pemodelan.
    """
    lebar = muat_lst().pivot(index="grid_id", columns="tahun", values="lst")
    return lebar.dropna()


@st.cache_data
def matriks_indeks() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Matriks NDVI dan NDBI per grid per tahun.

    Sejumlah kecil sel tidak memiliki citra bebas awan pada periode tertentu;
    nilainya diisi dengan interpolasi linear antartahun. Pengisian ini hanya
    dipakai untuk pemodelan, bukan untuk statistik deskriptif.
    """
    indeks = muat_indeks()
    ndvi = indeks.pivot(index="grid_id", columns="tahun", values="ndvi")
    ndbi = indeks.pivot(index="grid_id", columns="tahun", values="ndbi")
    isi = lambda m: m.interpolate(axis=1, limit_direction="both")
    return isi(ndvi), isi(ndbi)


@st.cache_data
def muat_evaluasi_cluster() -> pd.DataFrame:
    """Metrik internal clustering untuk k = 2..7, hasil asli penelitian."""
    return pd.read_csv(DATA / "evaluasi_cluster.csv")


@st.cache_data
def muat_evaluasi_model() -> pd.DataFrame:
    """Evaluasi 4 konfigurasi model x 2 algoritma, hasil asli penelitian."""
    return pd.read_csv(DATA / "evaluasi_model.csv")


@st.cache_data
def muat_definisi_model() -> pd.DataFrame:
    """Deskripsi tiap konfigurasi model M1 - M4."""
    return pd.read_csv(DATA / "definisi_model.csv")


# Kolom prediksi pada berkas hasil, dipetakan ke (kode konfigurasi, algoritma).
KOLOM_PREDIKSI_UJI = {
    "pred_M1_LagLST_RF": ("M1", "RF"),
    "pred_M1_LagLST_SVR": ("M1", "SVR"),
    "pred_M2_LagLST_byCluster_RF": ("M2", "RF"),
    "pred_M2_LagLST_byCluster_SVR": ("M2", "SVR"),
    "pred_M3_LagAll_RF": ("M3", "RF"),
    "pred_M3_LagAll_SVR": ("M3", "SVR"),
    "pred_M4_LagAll_byCluster_RF": ("M4", "RF"),
    "pred_M4_LagAll_byCluster_SVR": ("M4", "SVR"),
}


@st.cache_data
def muat_prediksi_uji() -> pd.DataFrame:
    """Prediksi LST 2024 tiap grid uji untuk 8 konfigurasi model, hasil penelitian.

    Berkas ``all_predictions_test_set.csv`` menyimpan LST aktual 2024, label
    klaster (kolom ``Cluster``), dan dugaan tiap konfigurasi (M1 - M4 x
    RF/SVR) untuk grid yang menjadi data uji. Dikembalikan dalam format
    panjang: satu baris per grid per konfigurasi.
    """
    mentah = pd.read_csv(DATA / "all_predictions_test_set.csv")
    mentah = mentah.rename(columns={"lst_2024": "aktual", "Cluster": "cluster"})
    if "cluster" not in mentah.columns:
        # Berkas lama tanpa kolom klaster: ambil dari label K-Means terpisah.
        peta = muat_cluster().set_index("grid_id")["k-means_cluster"]
        mentah["cluster"] = mentah["grid_id"].map(peta)

    panjang = mentah.melt(
        id_vars=["grid_id", "cluster", "aktual"],
        value_vars=list(KOLOM_PREDIKSI_UJI),
        var_name="kolom",
        value_name="prediksi",
    )
    petakan = panjang["kolom"].map(KOLOM_PREDIKSI_UJI)
    panjang["kode"] = petakan.str[0]
    panjang["algoritma"] = petakan.str[1]
    panjang["cluster"] = panjang["cluster"].astype("Int64")
    return panjang[["grid_id", "cluster", "kode", "algoritma", "aktual", "prediksi"]]
    

# --- Wilayah administrasi tiap grid ----------------------------------------

# CRS metrik untuk wilayah Jakarta dan sekitarnya; dipakai saat menghitung
# luas irisan agar perbandingannya tidak bias oleh lintang.
CRS_METRIK = "EPSG:32748"


@st.cache_data(show_spinner="Memuat batas wilayah ...")
def _batas_kecamatan() -> gpd.GeoDataFrame:
    """Batas kecamatan DKI Jakarta."""
    gdf = gpd.read_file(DATA / "batas" / "jakartacamat.shp")[["WADMKC", "WADMKK", "geometry"]]
    gdf = gdf.rename(columns={"WADMKC": "kecamatan", "WADMKK": "kota"})
    # "Kota Adm. Jakarta Timur" terlalu panjang untuk keterangan di peta.
    gdf["kota"] = gdf["kota"].str.replace("Kota Adm. ", "", regex=False)
    return gdf.to_crs("EPSG:4326")


@st.cache_data(show_spinner="Memuat batas wilayah ...")
def _batas_kabupaten() -> gpd.GeoDataFrame:
    """Batas kabupaten dan kota se-Jabodetabek, dipakai di luar DKI Jakarta."""
    gdf = gpd.read_file(DATA / "batas" / "jabodetabek.shp")[["WADMKK", "WADMPR", "geometry"]]
    gdf = gdf.rename(columns={"WADMKK": "kota", "WADMPR": "provinsi"})
    return gdf.to_crs("EPSG:4326")


def _wilayah_terluas(grid: gpd.GeoDataFrame, batas: gpd.GeoDataFrame, kolom: list[str]) -> pd.DataFrame:
    """Untuk tiap grid, pilih wilayah yang irisan luasnya paling besar.

    Sebuah sel 1 x 1 km kerap memotong beberapa wilayah sekaligus, sehingga
    yang dipakai adalah wilayah tempat sebagian besar sel itu berada, bukan
    wilayah yang kebetulan memuat titik pusatnya.
    """
    irisan = gpd.overlay(
        grid.to_crs(CRS_METRIK), batas.to_crs(CRS_METRIK), how="intersection", keep_geom_type=True
    )
    if irisan.empty:
        return pd.DataFrame(columns=["grid_id", *kolom])

    irisan["luas"] = irisan.geometry.area
    terbesar = irisan.loc[irisan.groupby("grid_id")["luas"].idxmax()]
    return pd.DataFrame(terbesar[["grid_id", *kolom]]).reset_index(drop=True)


@st.cache_data(show_spinner="Memetakan grid ke wilayah administrasi ...")
def wilayah_grid() -> pd.DataFrame:
    """Nama wilayah administrasi tiap grid, untuk keterangan di peta.

    Grid di dalam DKI Jakarta memperoleh nama kecamatan; grid di luar Jakarta
    hanya sampai tingkat kabupaten atau kota karena batas kecamatan di luar
    Jakarta tidak tersedia. Berkas data sumber tidak diubah sama sekali;
    penamaan ini dihitung ulang tiap aplikasi dijalankan lalu disimpan di
    penyangga.
    """
    jakarta = muat_grid()[["grid_id", "geometry"]]
    jabodetabek = _grid_uhi_mentah()[["grid_id", "geometry"]]
    semua = pd.concat([jakarta, jabodetabek], ignore_index=True).drop_duplicates("grid_id")
    semua = gpd.GeoDataFrame(semua, geometry="geometry", crs="EPSG:4326")

    kecamatan = _wilayah_terluas(semua, _batas_kecamatan(), ["kecamatan", "kota"])
    hasil = semua[["grid_id"]].merge(kecamatan, on="grid_id", how="left")

    # Sisanya berada di luar DKI Jakarta; ditandai sampai kabupaten/kota saja.
    sisa = semua[semua["grid_id"].isin(hasil.loc[hasil["kecamatan"].isna(), "grid_id"])]
    if not sisa.empty:
        kabupaten = _wilayah_terluas(sisa, _batas_kabupaten(), ["kota", "provinsi"])
        peta_kota = kabupaten.set_index("grid_id")["kota"]
        kosong = hasil["kecamatan"].isna()
        hasil.loc[kosong, "kota"] = hasil.loc[kosong, "grid_id"].map(peta_kota)

    # Sisa grid yang tidak beririsan dengan wilayah darat mana pun seluruhnya
    # berada di utara garis pantai, yaitu di perairan Teluk Jakarta.
    hasil["wilayah"] = [
        f"{kec}, {kot}" if isinstance(kec, str) else (kot if isinstance(kot, str) else "Perairan Teluk Jakarta")
        for kec, kot in zip(hasil["kecamatan"], hasil["kota"])
    ]
    return hasil[["grid_id", "kecamatan", "kota", "wilayah"]]


# --- Intensitas Urban Heat Island ------------------------------------------

# Zona penyangga dihitung dari batas wilayah administrasi DKI Jakarta.
ZONA_UHI = {
    "urban": "Wilayah administrasi DKI Jakarta",
    "peri-urban": "Penyangga 0 – 10 km dari batas Jakarta",
    "rural": "Penyangga 10 – 25 km, dipakai sebagai acuan",
}

# Kelas intensitas UHI, berurutan dari paling sejuk ke paling panas.
KELAS_UHI = ["No UHI", "Weak", "Moderate", "Strong", "Extreme"]

RENTANG_UHI = {
    "No UHI": "< 0 °C",
    "Weak": "0 – 2 °C",
    "Moderate": "2 – 4 °C",
    "Strong": "4 – 6 °C",
    "Extreme": "> 6 °C",
}


@st.cache_data(show_spinner="Memuat data intensitas UHI ...")
def _grid_uhi_mentah() -> gpd.GeoDataFrame:
    """Isi berkas UHI apa adanya, tanpa tambahan kolom apa pun.

    Dipisahkan dari :func:`muat_uhi` supaya penamaan wilayah dapat memakai
    geometrinya tanpa memanggil dirinya sendiri.
    """
    gdf = gpd.read_file(DATA / "uhi_jabodetabek.geojson")
    return gdf.set_crs("EPSG:4326", allow_override=True)


@st.cache_data
def muat_uhi() -> gpd.GeoDataFrame:
    """Intensitas UHI tiap grid pada seluruh wilayah kajian Jabodetabek.

    Intensitas dihitung sebagai selisih LST grid terhadap rata-rata LST
    seluruh grid zona rural, lalu digolongkan ke lima kelas. Berkas ini
    mencakup wilayah yang jauh lebih luas daripada berkas lain di dashboard
    dan hanya tersedia untuk satu periode.
    """
    gdf = _grid_uhi_mentah().merge(wilayah_grid(), on="grid_id", how="left")
    gdf["klas_uhi"] = pd.Categorical(gdf["klas_uhi"], categories=KELAS_UHI, ordered=True)
    gdf["zona"] = pd.Categorical(gdf["zona"], categories=list(ZONA_UHI), ordered=True)
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")


@st.cache_data
def ringkas_uhi() -> pd.DataFrame:
    """Statistik intensitas UHI per zona, beserta susunan kelasnya."""
    gdf = muat_uhi()
    ringkas = (
        gdf.groupby("zona", observed=True)["uhi_intensity"]
        .agg(["size", "mean", "median", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "size": "grid",
                "mean": "rata",
                "median": "median",
                "min": "minimum",
                "max": "maksimum",
            }
        )
    )
    return ringkas


@st.cache_data
def komposisi_kelas_uhi() -> pd.DataFrame:
    """Porsi tiap kelas intensitas UHI di dalam masing-masing zona."""
    gdf = muat_uhi()
    hitung = (
        gdf.groupby(["zona", "klas_uhi"], observed=True)
        .size()
        .reset_index(name="grid")
    )
    total = hitung.groupby("zona", observed=True)["grid"].transform("sum")
    hitung["persen"] = hitung["grid"] / total * 100
    return hitung


# --- Hasil analisis SHAP ---------------------------------------------------

# Urutan tetap ketiga variabel agar warnanya konsisten di seluruh grafik.
URUTAN_VARIABEL = ["LST", "NDVI", "NDBI"]

# Berkas SHAP per klaster, dikunci pada konfigurasi modelnya.
BERKAS_SHAP_KLASTER = {
    "M4: Lag LST + NDVI + NDBI (per Cluster)": "true_vector_shap_cluster_M4_LagAll_byCluster.csv",
    "M2: Lag LST (per Cluster)": "true_vector_shap_cluster_M2_LagLST_byCluster.csv",
}


@st.cache_data
def muat_shap_ringkas() -> pd.DataFrame:
    """Vector SHAP tiap konfigurasi model, diringkas per variabel.

    Satu baris menyatakan satu variabel pada satu model: rata-rata besar
    kontribusi SHAP setelah digabung atas seluruh lag variabel tersebut,
    simpangan bakunya, porsi kontribusinya, serta lag yang paling berpengaruh.
    """
    df = pd.read_csv(DATA / "tabel_vector_shap_summary.csv")
    df = df.rename(
        columns={
            "Model": "model",
            "Variabel": "variabel",
            "Jumlah Lag": "jumlah_lag",
            "Vector SHAP (mean)": "shap_rata",
            "Vector SHAP (std)": "shap_std",
            "Kontribusi (%)": "kontribusi",
            "Lag Terkuat": "lag_terkuat",
            "SHAP Lag Terkuat": "shap_lag_terkuat",
        }
    )
    df["kode"] = df["model"].str.split(":").str[0].str.strip()
    df["variabel"] = pd.Categorical(df["variabel"], categories=URUTAN_VARIABEL, ordered=True)
    return df.sort_values(["kode", "variabel"]).reset_index(drop=True)


@st.cache_data
def muat_shap_klaster(konfigurasi: str) -> pd.DataFrame:
    """Sebaran vector SHAP per klaster untuk satu konfigurasi model.

    Selain rata-rata, berkas menyediakan median dan kuartil sehingga sebaran
    yang menceng dapat ditampilkan apa adanya, bukan hanya nilai tengahnya.
    """
    df = pd.read_csv(DATA / BERKAS_SHAP_KLASTER[konfigurasi])
    df = df.rename(
        columns={
            "cluster": "klaster",
            "variable": "variabel",
            "vector_shap_mean": "shap_rata",
            "vector_shap_std": "shap_std",
            "vector_shap_sem": "shap_sem",
            "vector_shap_q25": "q25",
            "vector_shap_q75": "q75",
            "vector_shap_median": "median",
            "vector_shap_pct": "kontribusi",
            "n_samples": "n_grid",
        }
    )
    df["variabel"] = pd.Categorical(df["variabel"], categories=URUTAN_VARIABEL, ordered=True)
    return df.sort_values(["klaster", "variabel"]).reset_index(drop=True)


def statistik(seri: pd.Series) -> dict[str, float]:
    """Ringkasan statistik deskriptif untuk satu variabel."""
    bersih = seri.dropna()
    return {
        "n": int(bersih.size),
        "min": float(bersih.min()),
        "maks": float(bersih.max()),
        "rata": float(bersih.mean()),
        "median": float(bersih.median()),
        "std": float(bersih.std()),
    }
