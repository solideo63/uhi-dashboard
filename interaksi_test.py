"""Uji kombinasi kontrol yang berisiko, terutama periode dengan data tidak lengkap."""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from streamlit.testing.v1 import AppTest

AKAR = Path(__file__).parent
gagal = 0


def periksa(nama: str, uji: AppTest) -> None:
    global gagal
    if uji.exception:
        gagal += 1
        print(f"[GAGAL] {nama}")
        for k in uji.exception:
            print(f"        {k.value}")
    else:
        catatan = [w.value.split(".")[0] for w in uji.warning]
        print(f"[OK]    {nama}" + (f"  -> peringatan: {catatan}" if catatan else ""))


# Halaman eksplorasi: setiap tahun x setiap variabel, termasuk NDVI/NDBI 2018.
for tahun in [2009, 2012, 2015, 2018, 2021, 2024]:
    for variabel in ["LST", "NDVI", "NDBI"]:
        uji = AppTest.from_file(str(AKAR / "views/eksplorasi.py"), default_timeout=300)
        uji.run()
        uji.selectbox[0].set_value(tahun)
        uji.radio[0].set_value(variabel)
        periksa(f"eksplorasi {tahun} {variabel}", uji.run())

# Halaman clustering: ketiga metode.
for metode in ["K-Means Euclidean", "DTW K-Means", "k-Shape"]:
    uji = AppTest.from_file(str(AKAR / "views/clustering.py"), default_timeout=300)
    uji.run()
    uji.radio[0].set_value(metode)
    periksa(f"clustering {metode}", uji.run())

# Halaman forecasting: prediksi tersimpan, cakupan grid, dan tiga lapisan peta.
uji = AppTest.from_file(str(AKAR / "views/forecasting.py"), default_timeout=600).run()
for cakupan in ["Data uji", "Seluruh grid (latih dan uji)"]:
    for lapisan in ["Prediksi − aktual", "LST prediksi 2024", "LST aktual 2024"]:
        uji.radio(key="forecast-cakupan").set_value(cakupan)
        uji.radio(key="forecast-peta").set_value(lapisan)
        periksa(f"forecast {cakupan} | {lapisan}", uji.run())


# Halaman SHAP: kedua konfigurasi model per klaster. M2 hanya memuat satu
# variabel sehingga jalur kodenya berbeda dari M4.
for konfigurasi in ["M4: Lag LST + NDVI + NDBI (per Cluster)", "M2: Lag LST (per Cluster)"]:
    uji = AppTest.from_file(str(AKAR / "views/shap.py"), default_timeout=300)
    uji.run()
    uji.radio[0].set_value(konfigurasi)
    periksa(f"shap {konfigurasi.split(':')[0]}", uji.run())

print("\nGagal:", gagal)
raise SystemExit(1 if gagal else 0)

