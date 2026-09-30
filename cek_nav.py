"""Selidiki ke mana navigasi Streamlit berpindah saat layar menyempit."""

import json

from playwright.sync_api import sync_playwright

PERIKSA = """
() => {
  const ambil = (sel) => [...document.querySelectorAll(sel)].map(e => {
    const k = e.getBoundingClientRect();
    const g = getComputedStyle(e);
    return {
      sel, testid: e.dataset.testid || null,
      lebar: Math.round(k.width), tinggi: Math.round(k.height),
      display: g.display, visibility: g.visibility, opacity: g.opacity,
      teks: (e.innerText || '').slice(0, 50).replace(/\\n/g, ' | '),
    };
  });
  return {
    lebar: window.innerWidth,
    navLink: ambil('[data-testid="stTopNavLink"]').length,
    navContainer: ambil('[data-testid="stTopNavLinkContainer"]').length,
    header: ambil('header[data-testid="stHeader"]'),
    sidebar: ambil('section[data-testid="stSidebar"]'),
    sidebarNav: ambil('[data-testid="stSidebarNav"]'),
    kontrolSidebar: ambil('[data-testid="stSidebarCollapsedControl"]'),
    tombolHeader: [...document.querySelectorAll('header button, header [role="button"]')].map(e => ({
      label: e.getAttribute('aria-label') || e.getAttribute('title') || (e.innerText || '').slice(0, 30),
      lebar: Math.round(e.getBoundingClientRect().width),
    })),
    semuaTestidHeader: (() => {
      const h = document.querySelector('header[data-testid="stHeader"]');
      if (!h) return [];
      return [...h.querySelectorAll('[data-testid]')].map(e => e.dataset.testid);
    })(),
    // Apakah ada elemen navigasi yang tersembunyi karena CSS kita?
    tersembunyi: [...document.querySelectorAll('[data-testid*="Nav"], [data-testid*="Sidebar"]')].map(e => ({
      testid: e.dataset.testid,
      display: getComputedStyle(e).display,
      lebar: Math.round(e.getBoundingClientRect().width),
    })),
  };
}
"""

with sync_playwright() as p:
    peramban = p.chromium.launch()
    for lebar in (390, 640, 820, 1000, 1180, 1440):
        laman = peramban.new_page(viewport={"width": lebar, "height": 900})
        laman.goto("http://localhost:8520/", wait_until="networkidle")
        laman.wait_for_timeout(7000)
        hasil = laman.evaluate(PERIKSA)
        print(f"=== lebar {lebar} ===")
        print(json.dumps(hasil, indent=1, ensure_ascii=False))
        print()
        laman.close()
    peramban.close()
