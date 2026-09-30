"""Ukur area gambar Plotly yang benar-benar dipakai data pada lebar ponsel."""
import json
import sys
from playwright.sync_api import sync_playwright

LEBAR = int(sys.argv[1]) if len(sys.argv) > 1 else 390
HAL = ["/", "/temporal", "/clustering", "/shap", "/forecasting"]

CEK = """
() => [...document.querySelectorAll('.js-plotly-plot')].map(g => {
  const k = g.getBoundingClientRect();
  const drag = g.querySelector('.nsewdrag') || g.querySelector('.bg');
  const d = drag ? drag.getBoundingClientRect() : null;
  const judul = g.querySelector('.gtitle');
  const mb = g.querySelector('.modebar-container') || g.querySelector('.modebar');
  return {
    lebarGrafik: Math.round(k.width), tinggiGrafik: Math.round(k.height),
    lebarPlot: d ? Math.round(d.width) : null, tinggiPlot: d ? Math.round(d.height) : null,
    persenLebar: d && k.width ? Math.round(d.width / k.width * 100) : null,
    judul: judul ? (judul.textContent || '').slice(0, 50) : null,
    modebarLebar: mb ? Math.round(mb.getBoundingClientRect().width) : null,
    modebarOpacity: mb ? getComputedStyle(mb).opacity : null,
    modebarDisplay: mb ? getComputedStyle(mb).display : null,
  };
}).filter(x => x.lebarGrafik > 0)
"""

hasil = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": LEBAR, "height": 844})
    for j in HAL:
        pg.goto("http://localhost:8520" + j, wait_until="load", timeout=60000)
        pg.wait_for_timeout(11000)
        hasil[j.strip("/") or "beranda"] = pg.evaluate(CEK)
    b.close()
print(json.dumps(hasil, indent=1, ensure_ascii=False))
