"""Tangkapan layar per elemen (grafik & tabel) pada lebar ponsel."""
import sys
from playwright.sync_api import sync_playwright

LEBAR = int(sys.argv[1]) if len(sys.argv) > 1 else 390
TUGAS = [
    ("/clustering", ".js-plotly-plot", 4, "clustering_wcss"),
    ("/temporal", ".js-plotly-plot", 4, "temporal_korelasi"),
    ("/forecasting", 'div[data-testid="stDataFrame"]', 0, "forecasting_tabel1"),
    ("/forecasting", 'div[data-testid="stDataFrame"]', 1, "forecasting_tabel2"),
    ("/", 'div[data-testid="stDataFrame"]', 1, "beranda_tabel2"),
    ("/", "iframe[data-testid=\"stCustomComponentV1\"]", 0, "beranda_peta"),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": LEBAR, "height": 844})
    terakhir = None
    for jalur, pemilih, idx, nama in TUGAS:
        if jalur != terakhir:
            pg.goto("http://localhost:8520" + jalur, wait_until="load", timeout=60000)
            pg.wait_for_timeout(11000)
            terakhir = jalur
        els = pg.query_selector_all(pemilih)
        if len(els) > idx:
            try:
                els[idx].scroll_into_view_if_needed()
                pg.wait_for_timeout(600)
                els[idx].screenshot(path=f"hasil_m390/el_{nama}_{LEBAR}.png")
                print("ok", nama)
            except Exception as e:  # noqa: BLE001
                print("gagal", nama, e)
        else:
            print("tidak ada", nama, len(els))
    b.close()
