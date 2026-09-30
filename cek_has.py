from playwright.sync_api import sync_playwright
UJI = """
() => {
  const dukung = CSS.supports('selector(body:has(a))');
  const adaTopNav = !!document.querySelector('[data-testid="stTopNavLink"]');
  const cocok = document.querySelectorAll('body:has([data-testid="stTopNavLink"]) section[data-testid="stSidebar"]').length;
  const tombolBuka = !!document.querySelector('[data-testid="stExpandSidebarButton"]');
  return { lebar: window.innerWidth, dukungHas: dukung, adaTopNav, sidebarTerpilihOlehAturan: cocok, tombolBuka };
}
"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (390, 768, 900, 1440):
        l = b.new_page(viewport={"width": w, "height": 900})
        l.goto("http://localhost:8520/", wait_until="networkidle"); l.wait_for_timeout(9000)
        print(l.evaluate(UJI))
        l.close()
    b.close()
