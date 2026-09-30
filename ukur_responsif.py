"""Ukur perilaku tata letak dashboard pada satu lebar layar tertentu.

Pemakaian:
    .venv\\Scripts\\python.exe ukur_responsif.py <lebar> <tinggi> [jalur] [dir_keluaran]

Contoh:
    .venv\\Scripts\\python.exe ukur_responsif.py 390 844 /eksplorasi hasil

Yang dilaporkan untuk tiap halaman: luapan mendatar, elemen yang lebih lebar
daripada layar, ukuran huruf terkecil, lebar peta dan grafik, serta tangkapan
layar halaman penuh.
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PANGKALAN = "http://localhost:8520"

PEMERIKSAAN = """
() => {
  const akar = document.scrollingElement || document.documentElement;
  const utama = document.querySelector('section[data-testid="stMain"]') || akar;
  const lebarLayar = window.innerWidth;

  const meluap = [];
  for (const el of document.querySelectorAll('body *')) {
    const k = el.getBoundingClientRect();
    if (k.width === 0 || k.height === 0) continue;
    if (k.right > lebarLayar + 1 || k.left < -1) {
      const jejak = el.tagName.toLowerCase()
        + (el.dataset.testid ? `[${el.dataset.testid}]` : '')
        + (el.className && typeof el.className === 'string'
            ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : '');
      meluap.push({ el: jejak, kiri: Math.round(k.left), kanan: Math.round(k.right),
                    lebar: Math.round(k.width), teks: (el.innerText || '').slice(0, 60) });
    }
  }

  const ukuranHuruf = new Map();
  for (const el of document.querySelectorAll('p, span, div, td, th, li, h1, h2, h3, button')) {
    if (!el.innerText || !el.innerText.trim()) continue;
    if (el.children.length > 0) continue;
    const px = parseFloat(getComputedStyle(el).fontSize);
    if (!ukuranHuruf.has(px)) ukuranHuruf.set(px, el.innerText.trim().slice(0, 40));
  }

  const ukur = (pemilih) => [...document.querySelectorAll(pemilih)].map(e => {
    const k = e.getBoundingClientRect();
    return { lebar: Math.round(k.width), tinggi: Math.round(k.height) };
  });

  const kartu = [...document.querySelectorAll('.kartu')].map(e => {
    const k = e.getBoundingClientRect();
    return { lebar: Math.round(k.width), tinggi: Math.round(k.height), atas: Math.round(k.top) };
  });
  const barisKartu = new Set(kartu.map(k => k.atas)).size;

  return {
    lebarLayar,
    lebarGulirDokumen: Math.round(akar.scrollWidth),
    lebarGulirUtama: Math.round(utama.scrollWidth),
    luapanMendatar: Math.round(akar.scrollWidth - lebarLayar),
    tinggiHalaman: Math.round(utama.scrollHeight),
    elemenMeluap: meluap.slice(0, 12),
    jumlahMeluap: meluap.length,
    hurufTerkecil: [...ukuranHuruf.entries()].sort((a, b) => a[0] - b[0]).slice(0, 4)
      .map(([px, contoh]) => ({ px, contoh })),
    peta: ukur('iframe[data-testid="stCustomComponentV1"]'),
    grafik: ukur('.js-plotly-plot'),
    tabel: ukur('div[data-testid="stDataFrame"]'),
    kartu: { jumlah: kartu.length, baris: barisKartu, lebarMin: kartu.length ? Math.min(...kartu.map(k => k.lebar)) : null },
    navTerlihat: !!document.querySelector('[data-testid="stTopNavLink"]'),
    jumlahNav: document.querySelectorAll('[data-testid="stTopNavLink"]').length,
    merekTerlihat: (() => {
      const h = document.querySelector('header[data-testid="stHeader"]');
      if (!h) return null;
      return getComputedStyle(h, '::before').display !== 'none';
    })(),
  };
}
"""

HALAMAN = ["/", "/eksplorasi", "/temporal", "/clustering", "/forecasting", "/shap"]


def main() -> None:
    lebar = int(sys.argv[1]) if len(sys.argv) > 1 else 1440
    tinggi = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    jalur = [sys.argv[3]] if len(sys.argv) > 3 and sys.argv[3] != "semua" else HALAMAN
    keluaran = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("hasil_ukur")
    keluaran.mkdir(parents=True, exist_ok=True)

    hasil = {}
    with sync_playwright() as p:
        peramban = p.chromium.launch()
        laman = peramban.new_page(viewport={"width": lebar, "height": tinggi})
        for j in jalur:
            laman.goto(PANGKALAN + j, wait_until="networkidle")
            laman.wait_for_timeout(9000)
            nama = j.strip("/") or "beranda"
            hasil[nama] = laman.evaluate(PEMERIKSAAN)
            laman.screenshot(path=str(keluaran / f"{nama}_{lebar}.png"), full_page=False)
        peramban.close()

    berkas = keluaran / f"ukuran_{lebar}.json"
    berkas.write_text(json.dumps(hasil, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(hasil, indent=2, ensure_ascii=False))
    print(f"\ntersimpan: {berkas}")


if __name__ == "__main__":
    main()
