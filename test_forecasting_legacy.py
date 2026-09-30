"""Verifikasi hasil notebook lama, pemetaan grid, dan kontrol halaman forecasting."""
import json
import unittest
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from streamlit.testing.v1 import AppTest

import uhi_forecast as forecast
import uhi_viz as viz


class ForecastLegacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info, cls.evaluation, cls.predictions = forecast.muat_hasil()

    def test_saved_model_reproduces_predictions_and_2024_features(self):
        artifact = joblib.load(forecast.OUTPUT / 'best_model.joblib')
        frame = pd.read_csv(forecast.OUTPUT / 'analysis_data.csv', dtype={'grid_id': str})
        features = artifact['features']
        if self.info['best_model'] in ['M3', 'M4']:
            self.assertIn('ndvi2024', features)
            self.assertIn('ndbi2024', features)
        self.assertNotIn('lst_2024', features)
        prediction = np.full(len(frame), np.nan)
        for label, estimator in artifact['models'].items():
            mask = frame['kmeans_cluster'].eq(int(label)).to_numpy() if label != 'global' else np.ones(len(frame), dtype=bool)
            prediction[mask] = estimator.predict(frame.loc[mask, features].to_numpy())
        exported = self.predictions.set_index('grid_id').loc[frame['grid_id'], 'prediksi']
        np.testing.assert_allclose(prediction, exported, atol=1e-10)
        self.assertEqual((self.info['best_model'], self.info['best_algorithm']), ('M4', 'RF'))

    def test_grid_alignment_residual_and_map(self):
        for only_test in [True, False]:
            grid = forecast.peta_prediksi(self.predictions, hanya_uji=only_test)
            expected = self.info['n_test'] if only_test else self.info['n_complete']
            self.assertEqual(int(grid['prediksi'].notna().sum()), expected)
            self.assertFalse(grid['grid_id'].duplicated().any())
            valid = grid.dropna(subset=['prediksi'])
            np.testing.assert_allclose(valid['selisih'], valid['prediksi']-valid['aktual'], atol=1e-10)
            if only_test:
                self.assertEqual(set(valid['split']), {'test'})
                self.assertAlmostEqual(r2_score(valid['aktual'], valid['prediksi']), self.info['test_r2'], places=10)
            limit = float(valid['selisih'].abs().max())
            map_object = viz.peta_forecasting(grid, 'selisih', (-limit, limit), forecast.batas_jakarta())
            html = map_object.get_root().render()
            self.assertIn('aktual_teks', html)
            self.assertIn('prediksi_teks', html)
            self.assertIn('selisih_teks', html)
            self.assertTrue(any(getattr(layer, 'layer_name', None) == 'Batas Jakarta'
                                for layer in map_object._children.values()))

    def test_projection_uses_m4_features_and_stops_at_2027(self):
        projected = forecast.proyeksi_m4()
        self.assertEqual(set(projected['tahun']), {2027})
        self.assertEqual(set(projected['grid_id']), set(self.predictions['grid_id']))
        artifact = joblib.load(forecast.OUTPUT / 'best_model.joblib')
        frame = pd.read_csv(forecast.OUTPUT / 'analysis_data.csv', dtype={'grid_id': str})
        future = frame[artifact['features']].copy()
        for column in future.columns:
            future[column] = frame[column[:-4] + str(min(int(column[-4:]) + 3, 2024))]
        for label, estimator in artifact['models'].items():
            mask = frame['kmeans_cluster'].eq(int(label))
            expected = estimator.predict(future.loc[mask].to_numpy())
            actual = projected.set_index('grid_id').loc[frame.loc[mask, 'grid_id'], 'lst']
            np.testing.assert_allclose(actual, expected)

    def test_cluster_colors_are_bound_to_labels(self):
        frame = pd.DataFrame({'tahun': [2018, 2021], 'Klaster 3': [37., 38.]})
        plot = viz.garis_tren(frame, 'tahun', {'Klaster 3': 'Klaster 3'}, '', 'LST')
        self.assertEqual(plot.data[0].line.color, viz.WARNA_CLUSTER[3])
        history = pd.DataFrame({'tahun': [2024], 'cluster': [3], 'lst': [37.]})
        future = pd.DataFrame({'tahun': [2027], 'cluster': [3], 'lst': [38.]})
        plot = viz.garis_forecast(history, future, 'cluster', '')
        self.assertTrue(all(trace.line.color == viz.WARNA_CLUSTER[3] for trace in plot.data))

    def test_forecast_page_and_controls(self):
        app = AppTest.from_file(str(Path(__file__).parent / 'views/forecasting.py'), default_timeout=180).run()
        self.assertFalse(app.exception, [e.value for e in app.exception])
        self.assertEqual(app.radio(key='forecast-cakupan').value, 'Data uji')
        self.assertEqual(app.radio(key='forecast-peta').value, 'Prediksi − aktual')
        app.radio(key='forecast-cakupan').set_value('Seluruh grid (latih dan uji)').run()
        self.assertFalse(app.exception, [e.value for e in app.exception])
        for option in ['LST prediksi 2024', 'LST aktual 2024']:
            app.radio(key='forecast-peta').set_value(option).run()
            self.assertFalse(app.exception, [e.value for e in app.exception])

    def test_notebook_executed_without_errors_or_repeated_training(self):
        path = Path(__file__).parent / 'sintaks/New_LST_RF_SVR_Regression_Colab.ipynb'
        notebook = json.loads(path.read_text(encoding='utf-8'))
        code = [c for c in notebook['cells'] if c['cell_type'] == 'code']
        self.assertTrue(all(c['execution_count'] is not None for c in code))
        self.assertFalse(any(o.get('output_type') == 'error' for c in code for o in c.get('outputs', [])))
        self.assertEqual(sum('def evaluate_model(' in ''.join(c['source']) for c in code), 1)
        self.assertEqual(sum('all_results,summary_rows = {},[]' in ''.join(c['source']) for c in code), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
