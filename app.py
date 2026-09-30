"""Titik masuk dashboard Urban Heat Island DKI Jakarta.

Berkas ini hanya mengatur navigasi; isi tiap halaman berada di ``views/``.
Navigasi diletakkan di atas, bukan di bilah sisi, supaya seluruh lebar layar
tersedia untuk peta dan grafik.

Jalankan dengan:  .venv\\Scripts\\streamlit.exe run app.py
"""

import streamlit as st

import uhi_ui as ui

ui.siapkan_aplikasi()

HALAMAN = [
    st.Page("views/beranda.py", title="Beranda", icon=":material/home:", default=True),
    st.Page("views/eksplorasi.py", title="Eksplorasi", icon=":material/map:"),
    st.Page("views/temporal.py", title="Perubahan Temporal", icon=":material/trending_up:"),
    st.Page("views/clustering.py", title="Clustering", icon=":material/scatter_plot:"),
    st.Page("views/forecasting.py", title="Forecasting", icon=":material/insights:"),
    st.Page("views/shap.py", title="Interpretasi SHAP", icon=":material/query_stats:"),
]

st.navigation(HALAMAN, position="top").run()
ui.kaki_aplikasi()
