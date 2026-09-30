"""Arahkan kursor ke tengah tiap peta lalu rekam isi tooltip yang muncul."""

import sys

from playwright.sync_api import sync_playwright

KELUARAN = sys.argv[1]
HALAMAN = [("eksplorasi", "/eksplorasi"), ("clustering", "/clustering"), ("uhi", "/")]

with sync_playwright() as p:
    peramban = p.chromium.launch()
    laman = peramban.new_page(viewport={"width": 1600, "height": 1000})

    for nama, jalur in HALAMAN:
        laman.goto("http://localhost:8520" + jalur, wait_until="networkidle")
        laman.wait_for_timeout(18000)

        petak = laman.locator("iframe[data-testid=stCustomComponentV1]").first
        # Peta bisa berada di bawah layar; wadah gulir Streamlit digeser dulu
        # supaya kursor benar-benar jatuh di atas peta.
        petak.scroll_into_view_if_needed()
        laman.wait_for_timeout(2500)
        kotak = petak.bounding_box()
        bingkai = laman.frame_locator("iframe[data-testid=stCustomComponentV1]").first

        # Beberapa titik dicoba: satu titik saja bisa jatuh di sela grid atau
        # tertutup lapisan garis batas yang digambar di atasnya.
        teks = "<tidak muncul di titik mana pun>"
        for pecahan_x, pecahan_y in [(0.5, 0.55), (0.3, 0.45), (0.65, 0.4), (0.42, 0.7)]:
            # Kursor disingkirkan dulu; bila ia sudah berada di titik tujuan,
            # perpindahan berikutnya tidak memicu peristiwa mouseover apa pun.
            laman.mouse.move(0, 0)
            laman.wait_for_timeout(300)
            laman.mouse.move(
                kotak["x"] + kotak["width"] * pecahan_x, kotak["y"] + kotak["height"] * pecahan_y
            )
            laman.wait_for_timeout(1600)
            petunjuk = bingkai.locator(".leaflet-tooltip")
            if petunjuk.count():
                teks = f"({pecahan_x}, {pecahan_y}) " + petunjuk.first.inner_text()
                break
        print(f"{nama:12s} -> {teks!r}")

        laman.screenshot(path=f"{KELUARAN}/hover_{nama}.png")

    peramban.close()
