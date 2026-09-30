"""Ambil tangkapan layar tiap halaman untuk pemeriksaan tata letak secara visual."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PANGKALAN = "http://localhost:8520"
KELUARAN = Path(sys.argv[1] if len(sys.argv) > 1 else "tangkapan")
KELUARAN.mkdir(exist_ok=True)

HALAMAN = [
    ("beranda", "/"),
    ("eksplorasi", "/eksplorasi"),
    ("temporal", "/temporal"),
    ("clustering", "/clustering"),
    ("forecasting", "/forecasting"),
    ("shap", "/shap"),
]

with sync_playwright() as p:
    peramban = p.chromium.launch()
    laman = peramban.new_page(viewport={"width": 1600, "height": 1100})
    for nama, jalur in HALAMAN:
        laman.goto(PANGKALAN + jalur, wait_until="networkidle")
        # Beri waktu peta Folium dan grafik Plotly selesai menggambar.
        laman.wait_for_timeout(6000)
        berkas = KELUARAN / f"{nama}.png"
        laman.screenshot(path=str(berkas), full_page=True)
        print(f"tersimpan: {berkas}")
    peramban.close()
