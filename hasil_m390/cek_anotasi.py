"""Ukur tumpang tindih anotasi penanda satelit di halaman temporal."""
import json
import sys
from playwright.sync_api import sync_playwright

LEBAR = int(sys.argv[1]) if len(sys.argv) > 1 else 390

CEK = """
() => [...document.querySelectorAll('.js-plotly-plot')].map(g => {
  const judul = (g.querySelector('.gtitle')?.textContent || '').slice(0,45);
  const anot = [...g.querySelectorAll('.annotation-text')].map(t => {
    const k = t.getBoundingClientRect();
    return {teks: t.textContent, kiri: Math.round(k.left), kanan: Math.round(k.right),
            atas: Math.round(k.top), lebar: Math.round(k.width)};
  });
  const tumpang = [];
  for (let i=0;i<anot.length;i++) for (let j=i+1;j<anot.length;j++) {
    const a=anot[i], b=anot[j];
    const ox = Math.min(a.kanan,b.kanan)-Math.max(a.kiri,b.kiri);
    if (ox > 0 && Math.abs(a.atas-b.atas) < 12) tumpang.push({a:a.teks, b:b.teks, tumpangPx: Math.round(ox)});
  }
  return {judul, anot, tumpang};
}).filter(x => x.anot.length)
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": LEBAR, "height": 844})
    pg.goto("http://localhost:8520/temporal", wait_until="load", timeout=60000)
    pg.wait_for_timeout(11000)
    print(json.dumps(pg.evaluate(CEK), indent=1, ensure_ascii=False))
    b.close()
