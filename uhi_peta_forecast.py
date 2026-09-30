"""Peta hasil regresi tersimpan; terpisah dari modul visual umum."""
import branca.colormap as cm
import folium
import pandas as pd
from uhi_viz import _peta_dasar, RAMPA, TINTA

def peta_forecasting(gdf, kolom, rentang, batas=None):
    """Aktual/prediksi berbagi skala; selisih memakai skala simetris dengan nol di tengah."""
    label = {'aktual': 'LST aktual 2024', 'prediksi': 'LST prediksi 2024',
             'selisih': 'Prediksi − aktual'}[kolom]
    colors = ['#2166ac', '#f7f7f7', '#b2182b'] if kolom == 'selisih' else RAMPA['lst']
    skala = cm.LinearColormap(colors=colors, vmin=rentang[0], vmax=rentang[1])
    peta = _peta_dasar(gdf)
    layer = gdf[['grid_id', 'wilayah', 'aktual', 'prediksi', 'selisih', 'split', 'geometry']].copy()
    for field in ('aktual', 'prediksi', 'selisih'):
        layer[f'{field}_teks'] = layer[field].map(lambda x: 'Tidak ditampilkan' if pd.isna(x) else f'{x:+.3f} °C' if field == 'selisih' else f'{x:.3f} °C')
    layer['kelompok'] = layer['split'].map({
        'train': 'Data latih', 'test': 'Data uji',
        'interpolasi': 'Prediksi tambahan (NDVI/NDBI interpolasi)',
    }).fillna('Di luar cakupan / tanpa riwayat LST')

    def gaya(feature):
        value = feature['properties'][kolom]
        return dict(fillColor='#deded8' if value is None else skala(value),
                    color='#ffffff', weight=.3, fillOpacity=.4 if value is None else .88)

    folium.GeoJson(layer, name=label, style_function=gaya,
        highlight_function=lambda _: {'weight': 1.5, 'color': TINTA},
        tooltip=folium.GeoJsonTooltip(
            fields=['grid_id', 'wilayah', 'kelompok', 'aktual_teks', 'prediksi_teks', 'selisih_teks'],
            aliases=['Grid', 'Wilayah', 'Sampel', 'LST aktual', 'LST prediksi', 'Prediksi − aktual'],
            sticky=False)).add_to(peta)
    if batas is not None:
        folium.GeoJson(batas.geometry.boundary, name='Batas Jakarta', interactive=False,
                       style_function=lambda _: {'color': TINTA, 'weight': 1.5}).add_to(peta)
    return peta

