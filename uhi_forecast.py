"""Hasil run notebook data lama untuk halaman Forecasting; tidak melatih ulang."""
from pathlib import Path
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import r2_score, mean_squared_error

import uhi_data as data

OUTPUT = data.DATA / 'output/regression_legacy'
FILES = ('best_model.json', 'summary_evaluation.csv', 'best_model_predictions.csv')


def muat_hasil():
    """Invalidate cache ketika hasil notebook berubah, termasuk pada sesi aktif."""
    paths = [OUTPUT / name for name in FILES]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError('Jalankan notebook data lama terlebih dahulu. File belum tersedia: ' + ', '.join(missing))
    signature = tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in paths)
    return _baca_hasil(signature)


@st.cache_data(show_spinner=False)
def _baca_hasil(signature):
    paths = [Path(item[0]) for item in signature]
    info = json.loads(paths[0].read_text(encoding='utf-8'))
    evaluation = pd.read_csv(paths[1])
    predictions = pd.read_csv(paths[2], dtype={'grid_id': str})
    required = {'grid_id', 'cluster', 'aktual', 'prediksi', 'selisih', 'split', 'model', 'algoritma'}
    if not required.issubset(predictions.columns) or predictions['grid_id'].duplicated().any():
        raise ValueError('Skema atau identitas grid hasil forecasting tidak valid.')
    if info.get('source') != 'legacy_pre_harmonization' or info.get('residual_definition') != 'prediction_minus_actual':
        raise ValueError('Hasil harus berasal dari notebook data lama, dengan selisih prediksi − aktual.')
    if not predictions['split'].isin(['train', 'test']).all():
        raise ValueError('Pembagian grid latih/uji tidak valid.')
    if not np.isfinite(predictions[['aktual', 'prediksi', 'selisih']].to_numpy()).all():
        raise ValueError('Prediksi mengandung nilai kosong.')
    if not predictions['model'].eq(info['best_model']).all() or not predictions['algoritma'].eq(info['best_algorithm']).all():
        raise ValueError('Model pada CSV berbeda dari metadata.')
    np.testing.assert_allclose(predictions['selisih'], predictions['prediksi']-predictions['aktual'], atol=1e-10)
    test = predictions[predictions['split'].eq('test')]
    if len(test) != info['n_test'] or len(predictions) != info['n_complete']:
        raise ValueError('Jumlah grid hasil berbeda dari metadata run.')
    np.testing.assert_allclose(r2_score(test['aktual'], test['prediksi']), info['test_r2'], atol=1e-10)
    np.testing.assert_allclose(np.sqrt(mean_squared_error(test['aktual'], test['prediksi'])), info['test_rmse'], atol=1e-10)
    selected = evaluation[(evaluation['Config'].eq(info['best_label'])) & (evaluation['Algorithm'].eq(info['best_algorithm']))]
    if len(selected) != 1 or abs(float(selected.iloc[0]['Test_R2'])-info['test_r2']) > 0.000051:
        raise ValueError('Tabel evaluasi berbeda dari prediksi model terbaik.')
    if (info['best_model'], info['best_algorithm']) != ('M4', 'RF'):
        raise ValueError('Dashboard memerlukan hasil model M4-RF.')
    return info, evaluation, predictions


@st.cache_data(show_spinner=False)
def geometri_jakarta():
    grid = gpd.read_file(data.DATA / 'FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson')[['grid_id', 'geometry']].drop_duplicates('grid_id').copy()
    grid['grid_id'] = grid['grid_id'].astype(str)
    if grid['grid_id'].duplicated().any():
        raise ValueError('Duplikat geometri grid data lama.')
    wilayah = data.wilayah_grid().copy()
    wilayah['grid_id'] = wilayah['grid_id'].astype(str)
    grid = grid.merge(wilayah[['grid_id', 'wilayah']], on='grid_id', how='left', validate='one_to_one')
    grid['wilayah'] = grid['wilayah'].fillna('Tidak diketahui')
    return grid.to_crs('EPSG:4326')


def peta_prediksi(predictions, hanya_uji=True):
    selected = predictions[predictions['split'].eq('test')] if hanya_uji else predictions
    grid = geometri_jakarta()
    if not set(selected['grid_id']).issubset(set(grid['grid_id'])):
        raise ValueError('Ada prediksi tanpa geometri Jakarta.')
    return grid.merge(selected, on='grid_id', how='left', validate='one_to_one')


@st.cache_data(show_spinner=False)
def batas_jakarta():
    batas = data._batas_kecamatan().dissolve().to_crs('EPSG:32748')
    # Detail 20 m cukup untuk peta grid 1 km dan mengurangi muatan GeoJSON browser.
    batas['geometry'] = batas.geometry.simplify(20, preserve_topology=True)
    return batas.to_crs('EPSG:4326')


@st.cache_data(show_spinner="Menghitung proyeksi M4-RF 2027 ...")
def _proyeksi_m4(signature):
    import joblib
    artifact = joblib.load(OUTPUT / 'best_model.joblib')
    frame = pd.read_csv(OUTPUT / 'analysis_data.csv', dtype={'grid_id': str})
    features = artifact['features']
    future = frame[features].copy()
    # Geser semua periode tiga tahun. Indeks 2027 diasumsikan tetap seperti 2024.
    for column in features:
        year = int(column[-4:])
        next_column = column[:-4] + str(min(year + 3, 2024))
        future[column] = frame[next_column]
    prediction = np.full(len(frame), np.nan)
    for label, estimator in artifact['models'].items():
        mask = frame['kmeans_cluster'].eq(int(label))
        prediction[mask] = estimator.predict(future.loc[mask, features].to_numpy())
    if not np.isfinite(prediction).all():
        raise ValueError('Proyeksi M4-RF tidak lengkap.')
    return pd.DataFrame(dict(grid_id=frame['grid_id'], tahun=2027,
                             lst=prediction, cluster=frame['kmeans_cluster'].astype(int)))


def proyeksi_m4():
    muat_hasil()
    paths = [OUTPUT / name for name in ('best_model.joblib', 'analysis_data.csv')]
    signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
    return _proyeksi_m4(signature)
