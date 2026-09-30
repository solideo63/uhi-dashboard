"""Komponen visual bersama: peta choropleth Folium dan grafik Plotly.

Palet warna dipisahkan menurut tugasnya. Klaster adalah identitas sehingga
memakai empat warna kategorikal sesuai gambar referensi pengguna,
disertai label klaster yang konsisten. LST, NDVI, dan NDBI adalah
besaran kontinu sehingga masing-masing memakai satu rona tunggal dari terang ke
gelap.
"""

from __future__ import annotations

import branca.colormap as cm
import folium
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go

# --- Palet -----------------------------------------------------------------

PERMUKAAN = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SEKUNDER = "#52514e"
TINTA_REDUP = "#898781"
GARIS_KISI = "#e1e0d9"
SUMBU = "#c3c2b7"

# Palet klaster sesuai referensi: biru, hijau, merah muda, ungu.
WARNA_CLUSTER = {1: "#9EAFE5", 2: "#8FD0B5", 3: "#F7ABAD", 4: "#D0AFE0"}

# Identitas variabel: LST biru, NDVI hijau, dan NDBI oranye.
WARNA_VARIABEL = {"LST": "#2a78d6", "NDVI": "#1baf7a", "NDBI": "#eb6834"}

# Kelas intensitas UHI bersifat berurutan, bukan sekadar identitas, sehingga
# empat kelas positif memakai satu rona merah dari terang ke gelap. Kelas
# "No UHI" bernilai negatif — lebih sejuk daripada rata-rata rural — sehingga
# diberi rona biru yang berlawanan agar batas nol terbaca sekali pandang.
WARNA_UHI = {
    "No UHI": "#2a78d6",
    "Weak": "#ef9077",
    "Moderate": "#dd6a4d",
    "Strong": "#bc3f24",
    "Extreme": "#7d2415",
}

# Rona tunggal terang -> gelap untuk tiap variabel kontinu.
RAMPA = {
    "lst": ["#fde4dd", "#f5a892", "#e26f52", "#c04227", "#7d2415"],
    "ndvi": ["#e4f2e2", "#a9d7a5", "#5fb168", "#2c8438", "#17561f"],
    "ndbi": ["#feedde", "#fdbe85", "#fd8d3c", "#e6550d", "#a63603"],
}

TATA_LETAK = dict(
    paper_bgcolor=PERMUKAAN,
    plot_bgcolor=PERMUKAAN,
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=TINTA_SEKUNDER),
    # Margin atas menyediakan ruang untuk judul dan satu baris legenda di
    # bawahnya, supaya keduanya tidak pernah bertumpuk.
    margin=dict(l=60, r=28, t=92, b=52),
    hoverlabel=dict(bgcolor=PERMUKAAN, bordercolor=SUMBU, font=dict(color=TINTA, size=12)),
    legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0, bgcolor="rgba(0,0,0,0)"),
)

SUMBU_GAYA = dict(
    showgrid=True,
    gridcolor=GARIS_KISI,
    gridwidth=1,
    zeroline=False,
    linecolor=SUMBU,
    tickfont=dict(color=TINTA_REDUP, size=12),
    title_font=dict(color=TINTA_SEKUNDER, size=13),
)


def _rapikan(fig: go.Figure, judul: str, sumbu_x: str, sumbu_y: str) -> go.Figure:
    """Terapkan gaya bersama pada sebuah figur Plotly."""
    fig.update_layout(
        title=dict(
            text=judul, font=dict(size=16, color=TINTA), x=0, xanchor="left", y=0.97, yanchor="top"
        ),
        **TATA_LETAK,
    )
    fig.update_xaxes(title=sumbu_x, **SUMBU_GAYA)
    fig.update_yaxes(title=sumbu_y, **SUMBU_GAYA)
    return fig


# --- Peta ------------------------------------------------------------------


# Basemap abu-abu muda dari Esri. Dipilih karena bebas kunci API dan cukup
# senyap sehingga tidak bersaing dengan warna choropleth di atasnya; basemap
# bawaan CartoDB kini menuntut kunci API dan menampilkan watermark.
UBIN = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
    "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
)
ATRIBUSI = "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"


def _peta_dasar(gdf: gpd.GeoDataFrame) -> folium.Map:
    batas = gdf.total_bounds
    peta = folium.Map(tiles=UBIN, attr=ATRIBUSI, control_scale=True)
    peta.fit_bounds([[batas[1], batas[0]], [batas[3], batas[2]]])
    return peta


def peta_kontinu(
    gdf: gpd.GeoDataFrame,
    kolom: str,
    label: str,
    rampa: list[str],
    satuan: str = "",
) -> folium.Map:
    """Choropleth untuk satu variabel kontinu (LST, NDVI, atau NDBI)."""
    sah = gdf[gdf[kolom].notna()]
    peta = _peta_dasar(gdf)

    if sah.empty:
        return peta

    # Skala hanya dipakai untuk mewarnai; keterangannya digambar di luar peta
    # oleh :func:`legenda_kontinu` supaya tidak menutupi petak di tepi atas.
    skala = cm.LinearColormap(
        colors=rampa, vmin=float(sah[kolom].min()), vmax=float(sah[kolom].max())
    )

    def gaya(fitur):
        nilai = fitur["properties"][kolom]
        if nilai is None:
            return {"fillColor": "#e1e0d9", "color": "#ffffff", "weight": 0.3, "fillOpacity": 0.45}
        return {"fillColor": skala(nilai), "color": "#ffffff", "weight": 0.3, "fillOpacity": 0.85}

    folium.GeoJson(
        sah[["wilayah", kolom, "geometry"]],
        style_function=gaya,
        highlight_function=lambda _: {"weight": 2, "color": TINTA},
        tooltip=folium.GeoJsonTooltip(
            fields=["wilayah", kolom],
            aliases=["Kecamatan", f"{label}{satuan}"],
            localize=True,
            sticky=False,
        ),
        name=label,
    ).add_to(peta)

    return peta


def legenda_kontinu(
    nilai: pd.Series, rampa: list[str], label: str, satuan: str = "", desimal: int = 2
) -> str:
    """Batang gradasi sebagai keterangan peta variabel kontinu.

    Digambar di atas peta, bukan melayang di dalamnya, supaya petak di tepi
    atas tidak tertutup dan bentuknya seragam dengan keterangan peta klaster
    maupun peta UHI.
    """
    bersih = nilai.dropna()
    bawah, atas = float(bersih.min()), float(bersih.max())
    henti = ", ".join(
        f"{warna} {indeks / (len(rampa) - 1) * 100:.0f}%" for indeks, warna in enumerate(rampa)
    )
    tanda = [bawah + (atas - bawah) * bagian for bagian in (0, 0.25, 0.5, 0.75, 1)]
    angka = "".join(f"<span>{t:.{desimal}f}</span>" for t in tanda)

    return (
        "<div style='padding:2px 0 12px'>"
        f"<div style='font-size:12.5px;font-weight:600;color:{TINTA};margin-bottom:7px'>"
        f"{label}{satuan}</div>"
        f"<div style='height:11px;border-radius:3px;background:linear-gradient(90deg,{henti});"
        "box-shadow:0 0 0 1px rgba(11,11,11,.10)'></div>"
        f"<div style='display:flex;justify-content:space-between;font-size:11.5px;"
        f"color:{TINTA_REDUP};margin-top:5px;font-variant-numeric:tabular-nums'>{angka}</div>"
        "</div>"
    )


def peta_forecasting(*args, **kwargs):
    from uhi_peta_forecast import peta_forecasting as render
    return render(*args, **kwargs)


def peta_cluster(gdf: gpd.GeoDataFrame, kolom: str, nama_metode: str) -> folium.Map:
    """Choropleth label klaster. Warna dipasangkan tetap ke nomor klaster."""
    sah = gdf[gdf[kolom].notna()].copy()
    sah[kolom] = sah[kolom].astype(int)
    peta = _peta_dasar(gdf)

    if sah.empty:
        return peta

    def gaya(fitur):
        nomor = int(fitur["properties"][kolom])
        return {
            "fillColor": WARNA_CLUSTER.get(nomor, "#898781"),
            "color": "#ffffff",
            "weight": 0.3,
            "fillOpacity": 0.85,
        }

    folium.GeoJson(
        sah[["wilayah", kolom, "geometry"]],
        style_function=gaya,
        highlight_function=lambda _: {"weight": 2, "color": TINTA},
        tooltip=folium.GeoJsonTooltip(
            fields=["wilayah", kolom],
            aliases=["Kecamatan", f"Klaster ({nama_metode})"],
            sticky=False,
        ),
        name=nama_metode,
    ).add_to(peta)

    return peta


def peta_uhi(gdf: gpd.GeoDataFrame, kolom_kelas: str = "klas_uhi") -> folium.Map:
    """Choropleth kelas intensitas UHI pada seluruh wilayah kajian.

    Batas zona penyangga digambar sebagai garis di atas isian kelas supaya
    terlihat mana grid yang berada di dalam wilayah administrasi Jakarta.
    """
    sah = gdf[gdf[kolom_kelas].notna()].copy()
    # Kolom bertipe kategori tidak selalu selamat saat diubah ke GeoJSON,
    # sehingga dijadikan teks biasa sebelum diserahkan ke Folium.
    for kolom in (kolom_kelas, "zona"):
        sah[kolom] = sah[kolom].astype(str)
    peta = _peta_dasar(gdf)

    if sah.empty:
        return peta

    def gaya(fitur):
        return {
            "fillColor": WARNA_UHI.get(fitur["properties"][kolom_kelas], "#898781"),
            "color": "#ffffff",
            "weight": 0.15,
            "fillOpacity": 0.85,
        }

    folium.GeoJson(
        sah[["wilayah", kolom_kelas, "zona", "uhi_intensity", "geometry"]],
        style_function=gaya,
        highlight_function=lambda _: {"weight": 2, "color": TINTA},
        tooltip=folium.GeoJsonTooltip(
            fields=["wilayah", "zona", "uhi_intensity", kolom_kelas],
            aliases=["Wilayah", "Zona", "Intensitas UHI (°C)", "Kategori"],
            localize=True,
            sticky=False,
        ),
        name="Intensitas UHI",
    ).add_to(peta)

    urban = sah[sah["zona"] == "urban"]
    if not urban.empty:
        # Hanya garis tepinya yang digambar, bukan poligon utuh: poligon
        # dengan isian tembus pandang tetap menadah kursor sehingga tooltip
        # sel di dalam Jakarta tidak pernah muncul. Lapisan ini juga dibuat
        # tidak interaktif agar tidak ikut menangkap peristiwa tetikus.
        folium.GeoJson(
            urban.dissolve().geometry.boundary,
            style_function=lambda _: {"color": TINTA, "weight": 1.6, "fillOpacity": 0},
            name="Batas DKI Jakarta",
            interactive=False,
        ).add_to(peta)

    return peta


def legenda_uhi(jumlah: pd.Series) -> str:
    """Legenda kelas UHI; warna selalu didampingi kategori, rentang, dan jumlah."""
    rentang = {
        "No UHI": "&lt; 0 °C",
        "Weak": "0 – 2 °C",
        "Moderate": "2 – 4 °C",
        "Strong": "4 – 6 °C",
        "Extreme": "&gt; 6 °C",
    }
    potongan = [
        "<div style='display:flex;gap:16px;flex-wrap:wrap;align-items:center;"
        f"font-size:12.5px;color:{TINTA_SEKUNDER};padding:6px 0'>"
    ]
    for kelas, warna in WARNA_UHI.items():
        n = int(jumlah.get(kelas, 0))
        potongan.append(
            f"<span style='display:inline-flex;align-items:center;gap:7px'>"
            f"<span style='width:13px;height:13px;border-radius:3px;background:{warna};"
            f"box-shadow:0 0 0 1px rgba(11,11,11,.10)'></span>"
            f"<b style='color:{TINTA};font-weight:600'>{kelas}</b> {rentang[kelas]} &middot; {n} grid</span>"
        )
    potongan.append("</div>")
    return "".join(potongan)


def legenda_cluster(jumlah: pd.Series) -> str:
    """Legenda klaster sebagai HTML; warna selalu didampingi label dan jumlah grid."""
    potongan = [
        "<div style='display:flex;gap:18px;flex-wrap:wrap;align-items:center;"
        "font-size:13px;color:#52514e;padding:6px 0'>"
    ]
    for nomor in sorted(jumlah.index):
        warna = WARNA_CLUSTER.get(int(nomor), "#898781")
        potongan.append(
            f"<span style='display:inline-flex;align-items:center;gap:7px'>"
            f"<span style='width:13px;height:13px;border-radius:3px;background:{warna};"
            f"box-shadow:0 0 0 1px rgba(11,11,11,.10)'></span>"
            f"Klaster {int(nomor)} &middot; {int(jumlah[nomor])} grid</span>"
        )
    potongan.append("</div>")
    return "".join(potongan)


# --- Grafik ----------------------------------------------------------------


def _renggangkan(titik: dict[str, float], rentang: float) -> dict[str, float]:
    """Geser label yang berdekatan agar tidak saling menimpa.

    Label ditata dari nilai terkecil ke terbesar dan didorong ke atas bila
    jaraknya kurang dari jarak minimum. Posisi label boleh sedikit menyimpang
    dari titik datanya karena tugasnya hanya menamai garis, bukan menyatakan
    nilai.
    """
    jarak_minimum = rentang * 0.075
    hasil: dict[str, float] = {}
    sebelumnya: float | None = None
    for nama, y in sorted(titik.items(), key=lambda pasangan: pasangan[1]):
        if sebelumnya is not None and y - sebelumnya < jarak_minimum:
            y = sebelumnya + jarak_minimum
        hasil[nama] = y
        sebelumnya = y
    return hasil


def garis_tren(
    df: pd.DataFrame,
    kolom_x: str,
    seri: dict[str, str],
    judul: str,
    sumbu_y: str,
    rentang_minimum: float | None = None,
) -> go.Figure:
    """Grafik garis satu sumbu. Titik akhir tiap seri diberi label langsung.

    ``rentang_minimum`` memaksa sumbu-y merentang paling tidak seluas nilai
    itu, dipusatkan pada data. Dipakai bila ragam nilainya kecil sehingga
    penskalaan otomatis akan memperbesar perubahan yang sebenarnya tipis dan
    membuat pembaca mengira ada lonjakan besar.
    """
    fig = go.Figure()
    warna = list(WARNA_CLUSTER.values())
    ujung: dict[str, float] = {}
    semua_nilai: list[float] = []

    for indeks, (nama, kolom) in enumerate(seri.items()):
        fig.add_trace(
            go.Scatter(
                x=df[kolom_x],
                y=df[kolom],
                name=nama,
                mode="lines+markers",
                line=dict(width=2, color=WARNA_CLUSTER[int(nama.split()[-1])] if nama.startswith("Klaster ") else WARNA_VARIABEL.get(nama.split()[0], warna[indeks % len(warna)])),
                marker=dict(size=9, line=dict(width=2, color=PERMUKAAN)),
                hovertemplate=f"{nama}: %{{y:.3f}}<extra></extra>",
            )
        )
        terisi = df[df[kolom].notna()]
        if not terisi.empty:
            ujung[nama] = float(terisi[kolom].iloc[-1])
            semua_nilai.extend(terisi[kolom].astype(float).tolist())

    # Label langsung hanya pada titik terakhir, bukan pada setiap titik.
    if ujung and semua_nilai:
        rentang = max(semua_nilai) - min(semua_nilai) or 1.0
        posisi = _renggangkan(ujung, rentang)
        x_akhir = df[kolom_x].iloc[-1]
        for nama, y in posisi.items():
            # Label memakai tinta teks, bukan warna seri; identitas dibawa oleh
            # garis berwarna yang berakhir tepat di sebelahnya.
            fig.add_annotation(
                x=x_akhir,
                y=y,
                text=f"  {nama}",
                showarrow=False,
                xanchor="left",
                font=dict(size=12, color=TINTA_SEKUNDER),
            )

    fig.update_layout(hovermode="x unified", showlegend=len(seri) >= 2)
    _rapikan(fig, judul, "Tahun", sumbu_y)
    fig.update_xaxes(tickmode="array", tickvals=df[kolom_x].tolist())

    # Jaga agar sumbu-y tidak menyempit ke ragam data yang kecil.
    if rentang_minimum and semua_nilai:
        bawah, atas = min(semua_nilai), max(semua_nilai)
        tengah = (bawah + atas) / 2
        lebar = max(atas - bawah, rentang_minimum)
        sisa = lebar * 0.12
        fig.update_yaxes(range=[tengah - lebar / 2 - sisa, tengah + lebar / 2 + sisa])
    # Sisakan ruang di kanan agar label tidak terpotong tepi grafik. Dipasang
    # setelah _rapikan karena gaya bersama menimpa seluruh margin.
    if ujung:
        fig.update_layout(margin_r=int(14 + 7.2 * max(len(n) for n in ujung)))
    return fig

def batang_kelompok(
    df: pd.DataFrame, kolom_x: str, seri: dict[str, str], judul: str, sumbu_y: str, desimal: int = 3
) -> go.Figure:
    """Batang berkelompok: membandingkan beberapa seri pada tiap kategori sumbu-x."""
    fig = go.Figure()
    warna = list(WARNA_CLUSTER.values())

    for indeks, (nama, kolom) in enumerate(seri.items()):
        fig.add_trace(
            go.Bar(
                x=df[kolom_x].astype(str),
                y=df[kolom],
                name=nama,
                marker=dict(color=WARNA_CLUSTER[int(nama.split()[-1])] if nama.startswith("Klaster ") else WARNA_VARIABEL.get(nama.split()[0], warna[indeks % len(warna)]), line=dict(width=2, color=PERMUKAAN), cornerradius=4),
                text=df[kolom].round(desimal),
                textposition="outside",
                textfont=dict(color=TINTA_SEKUNDER, size=11),
                hovertemplate=f"{nama}: %{{y:.4f}}<extra></extra>",
            )
        )

    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08, showlegend=len(seri) >= 2)
    return _rapikan(fig, judul, "", sumbu_y)

def histogram(nilai: pd.Series, judul: str, sumbu_x: str, warna: str) -> go.Figure:
    """Distribusi nilai satu variabel pada satu tahun."""
    fig = go.Figure(
        go.Histogram(
            x=nilai.dropna(),
            nbinsx=32,
            marker=dict(color=warna, line=dict(width=2, color=PERMUKAAN)),
            hovertemplate="%{x}<br>%{y} grid<extra></extra>",
        )
    )
    fig.update_layout(showlegend=False, bargap=0.02)
    return _rapikan(fig, judul, sumbu_x, "Jumlah grid")


def batang_perbandingan(
    df: pd.DataFrame, kolom_kategori: str, kolom_nilai: str, judul: str, sumbu_y: str, warna: str
) -> go.Figure:
    """Batang tunggal dengan ujung membulat pada sisi data."""
    fig = go.Figure(
        go.Bar(
            x=df[kolom_kategori].astype(str),
            y=df[kolom_nilai],
            marker=dict(color=warna, line=dict(width=2, color=PERMUKAAN), cornerradius=4),
            text=df[kolom_nilai].round(3),
            textposition="outside",
            textfont=dict(color=TINTA_SEKUNDER, size=12),
            hovertemplate="%{x}: %{y:.4f}<extra></extra>",
        )
    )
    fig.update_layout(showlegend=False)
    return _rapikan(fig, judul, "", sumbu_y)


def sebar_prediksi(y_asli: pd.Series, y_duga: pd.Series, judul: str, warna: str) -> go.Figure:
    """Sebaran nilai aktual terhadap nilai dugaan, dengan garis identitas."""
    batas_bawah = float(min(y_asli.min(), y_duga.min())) - 0.3
    batas_atas = float(max(y_asli.max(), y_duga.max())) + 0.3

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[batas_bawah, batas_atas],
            y=[batas_bawah, batas_atas],
            mode="lines",
            name="Prediksi sempurna",
            line=dict(width=2, color=SUMBU, dash="dash"),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=y_asli,
            y=y_duga,
            mode="markers",
            name="Grid uji",
            marker=dict(size=8, color=warna, opacity=0.7, line=dict(width=1, color=PERMUKAAN)),
            hovertemplate="Aktual %{x:.2f} °C<br>Prediksi %{y:.2f} °C<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True)
    _rapikan(fig, judul, "LST aktual 2024 (°C)", "LST prediksi 2024 (°C)")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


def komposisi(
    df: pd.DataFrame,
    kolom_baris: str,
    kolom_seri: str,
    kolom_nilai: str,
    warna: dict[str, str],
    judul: str,
    sumbu_x: str,
    label_baris: str = "",
) -> go.Figure:
    """Batang bertumpuk 100%: susunan porsi tiap seri pada satu baris.

    Dipakai untuk membandingkan susunan penjelas SHAP antarmodel maupun
    susunan kelas intensitas UHI antarzona. Segmen yang terlalu tipis tidak
    diberi label agar angkanya tidak tumpang tindih; nilainya tetap terbaca
    lewat tetikus dan lewat tabel.
    """
    baris = list(dict.fromkeys(df[kolom_baris]))
    fig = go.Figure()

    for seri, rona in warna.items():
        potong = df[df[kolom_seri] == seri]
        if potong.empty:
            continue
        nilai = [
            float(potong[potong[kolom_baris] == b][kolom_nilai].iloc[0])
            if not potong[potong[kolom_baris] == b].empty
            else 0.0
            for b in baris
        ]
        fig.add_trace(
            go.Bar(
                y=[str(b) for b in baris],
                x=nilai,
                name=seri,
                orientation="h",
                marker=dict(color=rona, line=dict(width=2, color=PERMUKAAN), cornerradius=4),
                text=[f"{v:.1f}%" if v >= 8 else "" for v in nilai],
                textposition="inside",
                insidetextfont=dict(color=PERMUKAAN, size=12),
                hovertemplate=f"{seri}: %{{x:.2f}}%<extra></extra>",
            )
        )

    # Plotly membalik urutan legenda pada batang bertumpuk horizontal; urutan
    # legenda dikembalikan agar sama dengan urutan segmen dari kiri ke kanan.
    fig.update_layout(barmode="stack", bargap=0.32, legend_traceorder="normal")
    _rapikan(fig, judul, sumbu_x, label_baris)
    fig.update_xaxes(range=[0, 100], ticksuffix="%")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def besaran_shap(df: pd.DataFrame, kolom_baris: str, judul: str, label_baris: str = "") -> go.Figure:
    """Besar kontribusi SHAP dalam satuan aslinya (°C), bukan porsi.

    Batang bersebelahan agar besaran mutlak antarbaris dapat dibandingkan;
    porsi persentase sudah ditangani grafik komposisi.
    """
    baris = list(dict.fromkeys(df[kolom_baris]))
    fig = go.Figure()

    for variabel, warna in WARNA_VARIABEL.items():
        potong = df[df["variabel"] == variabel]
        if potong.empty:
            continue
        nilai = [
            float(potong[potong[kolom_baris] == b]["shap_rata"].iloc[0])
            if not potong[potong[kolom_baris] == b].empty
            else 0.0
            for b in baris
        ]
        fig.add_trace(
            go.Bar(
                x=[str(b) for b in baris],
                y=nilai,
                name=variabel,
                marker=dict(color=warna, line=dict(width=2, color=PERMUKAAN), cornerradius=4),
                text=[f"{v:.3f}" if v else "" for v in nilai],
                textposition="outside",
                textfont=dict(color=TINTA_SEKUNDER, size=11),
                hovertemplate=f"{variabel}: %{{y:.4f}} °C<extra></extra>",
            )
        )

    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    return _rapikan(fig, judul, label_baris, "Rata-rata |SHAP| (°C)")


def sebaran_shap(df: pd.DataFrame, judul: str) -> go.Figure:
    """Median dan rentang antarkuartil vector SHAP tiap klaster.

    Rata-rata ikut digambar karena sebarannya menceng: pada beberapa klaster
    rata-rata jauh di atas median, yang berarti sebagian kecil grid menyumbang
    kontribusi jauh lebih besar daripada grid lainnya.
    """
    fig = go.Figure()
    df = df.copy()
    # Tiap pasangan klaster-variabel menempati barisnya sendiri supaya titik
    # yang nilainya berdekatan tidak saling menimpa.
    df["baris"] = "Klaster " + df["klaster"].astype(str) + " · " + df["variabel"].astype(str)
    urutan = df.sort_values(["klaster", "variabel"])["baris"].tolist()

    for variabel, warna in WARNA_VARIABEL.items():
        potong = df[df["variabel"] == variabel]
        if potong.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=potong["median"],
                y=potong["baris"],
                name=variabel,
                mode="markers",
                marker=dict(size=11, color=warna, line=dict(width=2, color=PERMUKAAN)),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=potong["q75"] - potong["median"],
                    arrayminus=potong["median"] - potong["q25"],
                    color=warna,
                    thickness=2,
                    width=6,
                ),
                hovertemplate=(
                    f"{variabel}<br>median %{{x:.3f}} °C"
                    "<br>kuartil %{customdata[0]:.3f} – %{customdata[1]:.3f}"
                    "<br>rata-rata %{customdata[2]:.3f}<extra></extra>"
                ),
                customdata=potong[["q25", "q75", "shap_rata"]].to_numpy(),
            )
        )

    # Rata-rata cukup satu entri legenda karena tanda dan warnanya sama.
    fig.add_trace(
        go.Scatter(
            x=df["shap_rata"],
            y=df["baris"],
            name="Rata-rata",
            mode="markers",
            marker=dict(size=9, symbol="x-thin", line=dict(width=2, color=TINTA_SEKUNDER)),
            hovertemplate="rata-rata %{x:.3f} °C<extra></extra>",
        )
    )

    _rapikan(fig, judul, "Vector SHAP (°C)", "")
    fig.update_yaxes(
        categoryorder="array", categoryarray=urutan, autorange="reversed", showgrid=False
    )
    fig.update_xaxes(rangemode="tozero")
    return fig


def garis_forecast(
    riwayat: pd.DataFrame, ramalan: pd.DataFrame, kolom_seri: str, judul: str
) -> go.Figure:
    """Deret historis (garis penuh) disambung ramalan (garis putus-putus)."""
    fig = go.Figure()
    warna = list(WARNA_CLUSTER.values())

    for indeks, nama in enumerate(sorted(riwayat[kolom_seri].unique())):
        rona = WARNA_CLUSTER[int(nama)]
        h = riwayat[riwayat[kolom_seri] == nama]
        r = ramalan[ramalan[kolom_seri] == nama]
        # Ramalan disambungkan dari titik historis terakhir agar tidak terputus.
        sambung = pd.concat([h.tail(1), r], ignore_index=True)

        fig.add_trace(
            go.Scatter(
                x=h["tahun"],
                y=h["lst"],
                name=f"Klaster {nama}",
                mode="lines+markers",
                line=dict(width=2, color=rona),
                marker=dict(size=9, line=dict(width=2, color=PERMUKAAN)),
                legendgroup=str(nama),
                hovertemplate=f"Klaster {nama} - historis: %{{y:.2f}} °C<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=sambung["tahun"],
                y=sambung["lst"],
                name=f"Klaster {nama} (ramalan)",
                mode="lines+markers",
                line=dict(width=2, color=rona, dash="dot"),
                marker=dict(size=9, symbol="diamond", line=dict(width=2, color=PERMUKAAN)),
                legendgroup=str(nama),
                showlegend=False,
                hovertemplate=f"Klaster {nama} - ramalan: %{{y:.2f}} °C<extra></extra>",
            )
        )

    fig.update_layout(hovermode="x unified")
    _rapikan(fig, judul, "Tahun", "Rata-rata LST (°C)")
    tahun = sorted(set(riwayat["tahun"]) | set(ramalan["tahun"]))
    fig.update_xaxes(tickmode="array", tickvals=tahun)
    return fig
