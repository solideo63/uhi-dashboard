"""Jalankan tiap halaman secara headless dan laporkan bila ada yang gagal dirender."""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from streamlit.testing.v1 import AppTest

AKAR = Path(__file__).parent
HALAMAN = sorted((AKAR / "views").glob("*.py"))

gagal = 0
for berkas in HALAMAN:
    uji = AppTest.from_file(str(berkas), default_timeout=300).run()
    if uji.exception:
        gagal += 1
        print(f"[GAGAL] {berkas.name}")
        for kesalahan in uji.exception:
            print(f"        {kesalahan.value}")
    else:
        print(
            f"[OK]    {berkas.name:38s} "
            f"{len(uji.markdown)} markdown, {len(uji.dataframe)} tabel, "
            f"{len(uji.warning)} peringatan"
        )

print("\nGagal:" , gagal, "dari", len(HALAMAN), "halaman")
raise SystemExit(1 if gagal else 0)

