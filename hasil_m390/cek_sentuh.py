"""Ukur luas sasaran sentuh radio & toolbar tabel pada lebar ponsel."""
import json
from playwright.sync_api import sync_playwright

CEK = """
() => {
  const r = [...document.querySelectorAll('label[data-baseweb="radio"]')].map(e => {
    const k = e.getBoundingClientRect();
    return {teks: (e.innerText||'').trim(), w: Math.round(k.width), h: Math.round(k.height)};
  });
  const sel = [...document.querySelectorAll('div[data-testid="stSelectbox"] [role="combobox"], div[data-baseweb="select"]')].map(e => {
    const k = e.getBoundingClientRect();
    return {w: Math.round(k.width), h: Math.round(k.height)};
  });
  return {radio: r, selectbox: sel};
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto("http://localhost:8520/eksplorasi", wait_until="load", timeout=60000)
    pg.wait_for_timeout(11000)
    print(json.dumps(pg.evaluate(CEK), indent=1, ensure_ascii=False))
    b.close()
