"""Selidiki nasib navigasi atas pada lebar ponsel."""
import json
import sys
from playwright.sync_api import sync_playwright

LEBAR = int(sys.argv[1]) if len(sys.argv) > 1 else 390
TINGGI = int(sys.argv[2]) if len(sys.argv) > 2 else 844

CEK = """
() => {
  const info = {};
  const h = document.querySelector('header[data-testid="stHeader"]');
  info.header = h ? {rect: h.getBoundingClientRect().toJSON(), html: h.outerHTML.slice(0, 1500)} : null;
  info.topNavLink = document.querySelectorAll('[data-testid="stTopNavLink"]').length;
  info.topNavAny = [...document.querySelectorAll('[data-testid*="TopNav" i], [data-testid*="Nav" i]')]
    .map(e => ({tid: e.dataset.testid, disp: getComputedStyle(e).display,
                vis: getComputedStyle(e).visibility, rect: e.getBoundingClientRect().toJSON(),
                teks: (e.innerText||'').slice(0,120)}));
  const sb = document.querySelector('section[data-testid="stSidebar"]');
  info.sidebar = sb ? {disp: getComputedStyle(sb).display, vis: getComputedStyle(sb).visibility,
                       rect: sb.getBoundingClientRect().toJSON(),
                       teks: (sb.innerText||'').slice(0,300),
                       ariaExpanded: sb.getAttribute('aria-expanded')} : null;
  const cc = document.querySelector('div[data-testid="stSidebarCollapsedControl"]');
  info.collapsedControl = cc ? {disp: getComputedStyle(cc).display, rect: cc.getBoundingClientRect().toJSON()} : null;
  // semua tombol di header
  info.tombolHeader = h ? [...h.querySelectorAll('button, a')].map(e => ({
      tag: e.tagName, tid: e.dataset.testid, label: e.getAttribute('aria-label'),
      teks: (e.innerText||'').trim().slice(0,40), rect: e.getBoundingClientRect().toJSON(),
      disp: getComputedStyle(e).display})) : [];
  // tautan halaman di mana pun
  info.pageLinks = [...document.querySelectorAll('[data-testid="stSidebarNavLink"], a[href^="/"]')]
    .map(e => ({tid: e.dataset.testid, href: e.getAttribute('href'), teks: (e.innerText||'').trim().slice(0,40),
                rect: e.getBoundingClientRect().toJSON(),
                terlihat: !!(e.getBoundingClientRect().width && e.getBoundingClientRect().height)}));
  return info;
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": LEBAR, "height": TINGGI})
    pg.goto("http://localhost:8520/", wait_until="load", timeout=60000)
    pg.wait_for_timeout(12000)
    hasil = {"awal": pg.evaluate(CEK)}

    # coba klik tombol pembuka bilah sisi bila ada
    try:
        tombol = pg.query_selector('header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"]') \
            or pg.query_selector('header[data-testid="stHeader"] button[aria-label*="sidebar" i]') \
            or pg.query_selector('header[data-testid="stHeader"] button')
        if tombol:
            hasil["tombolDiklik"] = {
                "tid": tombol.get_attribute("data-testid"),
                "label": tombol.get_attribute("aria-label"),
            }
            tombol.click()
            pg.wait_for_timeout(2500)
            hasil["setelahKlik"] = pg.evaluate(CEK)
            pg.screenshot(path="hasil_m390/setelah_klik_%d.png" % LEBAR)
    except Exception as e:  # noqa: BLE001
        hasil["galatKlik"] = str(e)

    b.close()

print(json.dumps(hasil, indent=2, ensure_ascii=False))
