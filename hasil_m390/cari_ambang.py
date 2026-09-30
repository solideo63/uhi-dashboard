"""Cari ambang lebar layar tempat navigasi atas Streamlit muncul/hilang."""
import json
from playwright.sync_api import sync_playwright

CEK = """
() => ({
  n: document.querySelectorAll('[data-testid="stTopNavLink"]').length,
  sb: document.querySelectorAll('[data-testid="stSidebarNavLink"]').length,
  lebar: window.innerWidth,
})
"""

hasil = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto("http://localhost:8520/", wait_until="load", timeout=60000)
    pg.wait_for_timeout(12000)
    for w in [360, 390, 430, 480, 540, 600, 640, 700, 768, 800, 900, 1024, 1180, 1280, 1440]:
        pg.set_viewport_size({"width": w, "height": 844})
        pg.wait_for_timeout(1800)
        hasil.append(pg.evaluate(CEK))
    b.close()
print(json.dumps(hasil, indent=1))
