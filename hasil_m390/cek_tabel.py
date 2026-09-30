"""Periksa keterbacaan tabel & tangkapan layar penuh pada lebar ponsel."""
import json
import sys
from playwright.sync_api import sync_playwright

LEBAR = int(sys.argv[1]) if len(sys.argv) > 1 else 390
HAL = ["/", "/eksplorasi", "/temporal", "/clustering", "/forecasting", "/shap"]

CEK = """
() => {
  const out = {tabel: [], plotly: [], sasaranKecil: [], toolbarPlotly: []};
  for (const t of document.querySelectorAll('div[data-testid="stDataFrame"]')) {
    const k = t.getBoundingClientRect();
    const stack = t.querySelector('.dvn-stack');
    const scroller = t.querySelector('.dvn-scroller') || t.querySelector('[class*="scroll"]');
    out.tabel.push({
      lebarTampil: Math.round(k.width),
      lebarIsi: stack ? Math.round(stack.getBoundingClientRect().width) : null,
      scrollWidth: scroller ? scroller.scrollWidth : null,
      clientWidth: scroller ? scroller.clientWidth : null,
      overflowX: scroller ? getComputedStyle(scroller).overflowX : null,
      bilahGulirTampak: scroller ? [...t.querySelectorAll('*')].some(e => {
        const s = getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return r.height > 0 && r.height < 20 && r.width > 50 && s.position === 'absolute';
      }) : null,
    });
  }
  for (const g of document.querySelectorAll('.js-plotly-plot')) {
    const k = g.getBoundingClientRect();
    const tick = g.querySelector('.xtick text');
    const legenda = g.querySelector('.legend');
    out.plotly.push({
      lebar: Math.round(k.width), tinggi: Math.round(k.height),
      xtickPx: tick ? parseFloat(getComputedStyle(tick).fontSize) : null,
      jumlahXtick: g.querySelectorAll('.xtick').length,
      legendaLebar: legenda ? Math.round(legenda.getBoundingClientRect().width) : null,
    });
    const mb = g.querySelector('.modebar');
    if (mb) out.toolbarPlotly.push({lebar: Math.round(mb.getBoundingClientRect().width),
                                    kanan: Math.round(mb.getBoundingClientRect().right)});
  }
  // sasaran sentuh < 44px
  for (const el of document.querySelectorAll('button, [role="tab"], input[type="radio"], select, [role="combobox"], summary')) {
    const k = el.getBoundingClientRect();
    if (k.width === 0 || k.height === 0) continue;
    if (k.height < 40) out.sasaranKecil.push({
      tag: el.tagName.toLowerCase(), tid: el.dataset.testid || el.getAttribute('role'),
      teks: (el.innerText || '').trim().slice(0, 30),
      w: Math.round(k.width), h: Math.round(k.height)});
  }
  out.sasaranKecil = out.sasaranKecil.slice(0, 10);
  return out;
}
"""

hasil = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": LEBAR, "height": 844})
    for j in HAL:
        pg.goto("http://localhost:8520" + j, wait_until="load", timeout=60000)
        pg.wait_for_timeout(11000)
        nama = j.strip("/") or "beranda"
        hasil[nama] = pg.evaluate(CEK)
        pg.screenshot(path=f"hasil_m390/penuh_{nama}_{LEBAR}.png", full_page=True)
    b.close()
print(json.dumps(hasil, indent=1, ensure_ascii=False))
