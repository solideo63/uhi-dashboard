"""Elemen antarmuka yang dipakai berulang di seluruh halaman dashboard.

Navigasi berada di atas pada desktop dan di bilah samping pada layar HP.
"""

from __future__ import annotations

import streamlit as st

import uhi_viz as viz

JUDUL_APLIKASI = "Dashboard Urban Heat Island DKI Jakarta"

_GAYA = f"""
<style>
  :root {{
    --tinta: {viz.TINTA};
    --tinta-2: {viz.TINTA_SEKUNDER};
    --tinta-redup: {viz.TINTA_REDUP};
    --permukaan: {viz.PERMUKAAN};
    --bidang: #edece5;
    --garis: rgba(11,11,11,.09);
    --aksen: {viz.WARNA_CLUSTER[1]};
  }}

  /* Streamlit memindahkan navigasi atas ke sidebar pada layar kecil.
     Sembunyikan sidebar hanya pada desktop agar menu HP tetap bisa dibuka. */
  @media (min-width: 769px) {{
    section[data-testid="stSidebar"], div[data-testid="stSidebarCollapsedControl"] {{
      display: none !important;
    }}
  }}

  .stApp {{ background: var(--bidang); }}
  .block-container {{ padding-top: 2.1rem; padding-bottom: 3.5rem; max-width: 1480px; }}

  /* --- Navigasi atas ------------------------------------------------------
     Nama aplikasi disisipkan sebagai butir pertama di dalam bilah navigasi.
     Bilah ini melekat di atas layar, sehingga apa pun yang digambar sebelum
     halaman dijalankan akan tertutup olehnya. */
  header[data-testid="stHeader"] {{
    background: var(--permukaan) !important;
    border-bottom: 1px solid var(--garis);
  }}
  header[data-testid="stHeader"]::before {{
    content: "{JUDUL_APLIKASI}";
    display: flex; align-items: center; flex: 0 0 auto;
    padding: 0 22px 0 20px; margin-right: 4px;
    font-size: 13.5px; font-weight: 650; color: var(--tinta);
    letter-spacing: -.01em; white-space: nowrap;
    border-right: 1px solid var(--garis);
  }}
  @media (max-width: 1180px) {{
    header[data-testid="stHeader"]::before {{ display: none; }}
  }}
  [data-testid="stTopNavLink"] {{
    font-size: 13.5px !important; font-weight: 500; border-radius: 8px;
  }}

  /* --- Judul halaman ---------------------------------------------------- */
  .judul-halaman {{ margin: 8px 0 4px; }}
  .judul-halaman .kelopak {{
    font-size: 11.5px; font-weight: 600; letter-spacing: .09em; text-transform: uppercase;
    color: var(--aksen); margin-bottom: 6px;
  }}
  .judul-halaman h1 {{
    font-size: 32px; font-weight: 680; color: var(--tinta);
    letter-spacing: -.022em; line-height: 1.18; margin: 0 0 10px;
  }}

  /* Paragraf pengantar tepat di bawah judul. Ukurannya lebih besar dan
     lebarnya dibatasi ~68 karakter agar terbaca sebagai satu blok utuh,
     bukan sebaris teks panjang dengan ruang kosong lebar di sisi kanan. */
  .pengantar {{
    font-size: 15px; color: var(--tinta-2); line-height: 1.72;
    max-width: 68ch; margin: 4px 0 18px; text-wrap: pretty;
  }}
  .pengantar b {{ color: var(--tinta); font-weight: 620; }}
  h2, h3 {{ color: var(--tinta); letter-spacing: -.012em; }}
  h2 {{ font-size: 21px !important; padding-top: 6px !important; }}
  h3 {{ font-size: 17px !important; }}

  /* --- Kartu statistik --------------------------------------------------- */
  .kartu-baris {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 6px 0 20px; }}
  .kartu {{
    flex: 1 1 160px; background: var(--permukaan); border-radius: 12px;
    padding: 15px 17px 16px; border: 1px solid var(--garis);
    transition: border-color .15s ease;
  }}
  .kartu:hover {{ border-color: rgba(11,11,11,.20); }}
  .kartu .label {{
    font-size: 11px; color: var(--tinta-redup); text-transform: uppercase;
    letter-spacing: .07em; font-weight: 600; margin-bottom: 8px;
  }}
  .kartu .nilai {{
    font-size: 28px; font-weight: 620; color: var(--tinta);
    line-height: 1.1; letter-spacing: -.02em;
  }}
  .kartu .catatan {{ font-size: 12px; color: var(--tinta-2); margin-top: 6px; line-height: 1.45; }}

  /* --- Kartu isi halaman -------------------------------------------------- */
  .kartu-isi-baris {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 6px 0 8px; }}
  .kartu-isi {{
    flex: 1 1 250px; background: var(--permukaan); border-radius: 12px;
    padding: 15px 17px 16px; border: 1px solid var(--garis);
  }}
  .kartu-isi .nama {{
    font-size: 14px; font-weight: 620; color: var(--tinta); margin-bottom: 6px;
  }}
  .kartu-isi .nama::before {{
    content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 2px;
    background: var(--aksen); margin-right: 8px; vertical-align: middle;
  }}
  .kartu-isi .isi {{ font-size: 12.5px; color: var(--tinta-2); line-height: 1.55; }}

  /* --- Teks penjelas ----------------------------------------------------- */
  .keterangan {{
    font-size: 13.5px; color: var(--tinta-2); line-height: 1.68;
    max-width: 92ch; margin: 2px 0 14px;
  }}
  .keterangan.catatan-samping {{
    border-left: 3px solid var(--garis); padding: 2px 0 2px 14px; margin-top: 12px;
  }}

  /* --- Komponen Streamlit ------------------------------------------------ */
  div[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
  div[data-testid="stElementContainer"] .js-plotly-plot {{
    border: 1px solid var(--garis); border-radius: 12px; background: var(--permukaan);
  }}
  /* Peta Folium adalah komponen pihak ketiga; penanda uji melekat pada
     elemen iframe itu sendiri, bukan pembungkusnya, sehingga bingkainya
     dipasang langsung di sana agar seragam dengan grafik Plotly. */
  iframe[data-testid="stCustomComponentV1"] {{
    border: 1px solid var(--garis) !important; border-radius: 12px;
    background: var(--permukaan);
  }}
  div[data-testid="stExpander"] details {{
    border: 1px solid var(--garis); border-radius: 10px; background: var(--permukaan);
  }}
  button[data-testid="stBaseButton-secondary"] {{ border-radius: 8px; }}
  div[data-testid="stTabs"] button[role="tab"] {{ font-size: 14px; }}
  hr {{ border-color: var(--garis); margin: 1.6rem 0 1.1rem; }}

  /* --- Kaki aplikasi ------------------------------------------------------ */
  .kaki {{
    margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--garis);
    font-size: 12px; color: var(--tinta-redup); line-height: 1.6;
  }}
</style>
"""


def siapkan_aplikasi() -> None:
    """Konfigurasi aplikasi. Hanya dipanggil sekali, dari ``app.py``."""
    st.set_page_config(
        page_title=JUDUL_APLIKASI,
        page_icon="🌡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(_GAYA, unsafe_allow_html=True)


def gaya_halaman() -> None:
    """Sisipkan gaya bersama. Dipanggil tiap halaman agar tetap rapi bila
    halaman itu dijalankan sendiri, misalnya saat pengujian."""
    st.markdown(_GAYA, unsafe_allow_html=True)


def kaki_aplikasi() -> None:
    """Catatan sumber di kaki halaman."""
    st.markdown(
        "<div class='kaki'>Sumber data: komposit Landsat puncak musim kemarau pada grid "
        "1 × 1 km, periode 2009–2024. Angka evaluasi clustering, evaluasi model, dan SHAP "
        "dibaca langsung dari berkas hasil penelitian.</div>",
        unsafe_allow_html=True,
    )


def judul_halaman(kelopak: str, judul: str, deskripsi: str = "") -> None:
    """Judul halaman: label kecil di atas, judul, lalu paragraf pengantar."""
    gaya_halaman()
    st.markdown(
        f"<div class='judul-halaman'><div class='kelopak'>{kelopak}</div><h1>{judul}</h1></div>",
        unsafe_allow_html=True,
    )
    if deskripsi:
        st.markdown(f"<p class='pengantar'>{deskripsi}</p>", unsafe_allow_html=True)


def kartu(butir: list[tuple[str, str, str]]) -> None:
    """Deretan kartu statistik: (label, nilai, catatan)."""
    potongan = ["<div class='kartu-baris'>"]
    for label, nilai, catatan in butir:
        potongan.append(
            f"<div class='kartu'><div class='label'>{label}</div>"
            f"<div class='nilai'>{nilai}</div>"
            f"<div class='catatan'>{catatan}</div></div>"
        )
    potongan.append("</div>")
    st.markdown("".join(potongan), unsafe_allow_html=True)


def kartu_isi(butir: list[tuple[str, str]]) -> None:
    """Kartu ringkas berisi nama halaman dan penjelasan singkatnya."""
    potongan = ["<div class='kartu-isi-baris'>"]
    for nama, isi in butir:
        potongan.append(
            f"<div class='kartu-isi'><div class='nama'>{nama}</div>"
            f"<div class='isi'>{isi}</div></div>"
        )
    potongan.append("</div>")
    st.markdown("".join(potongan), unsafe_allow_html=True)


def keterangan(teks: str, samping: bool = False) -> None:
    """Paragraf penjelas. ``samping`` memberi garis tepi untuk catatan tambahan."""
    kelas = "keterangan catatan-samping" if samping else "keterangan"
    st.markdown(f"<p class='{kelas}'>{teks}</p>", unsafe_allow_html=True)
