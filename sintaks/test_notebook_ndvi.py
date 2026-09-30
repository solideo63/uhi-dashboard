r"""Uji lokal notebook dengan fixture sintetis; tidak menghasilkan data penelitian.

Jalankan: .venv\Scripts\python.exe sintaks/test_notebook_ndvi.py
Dependensi: dependensi notebook, nbformat, esprima.
"""
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault('MPLBACKEND', 'Agg')
ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / 'New_LST_RF_SVR_Regression_Colab.landsat_v2.ipynb'


class NotebookIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use('Agg')
        import numpy as np
        import pandas as pd
        import geopandas as gpd
        from shapely.geometry import box
        import nbformat
        import esprima

        notebook = nbformat.read(NOTEBOOK, as_version=4)
        nbformat.validate(notebook)
        esprima.parseScript((ROOT / 'ndvi_ndbi_jkt.js').read_text(encoding='utf-8'))
        cls.sources = {cell['id']: cell['source'] for cell in notebook.cells if cell.cell_type == 'code'}
        for name, source in cls.sources.items():
            compile(source, name, 'exec')
        cls.temp = tempfile.TemporaryDirectory(prefix='ndvi_test_')
        cls.directory = Path(cls.temp.name)
        cls.ns = {'sys': sys, 'IN_COLAB': False, 'DATA_DIR_OVERRIDE': cls.directory / 'data'}
        old_cwd = Path.cwd()
        try:
            os.chdir(cls.directory)
            with open(cls.directory / 'execution.log', 'w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                exec(cls.sources['config'], cls.ns)
                ns = cls.ns
                ns['RF_PARAMS'] = dict(n_estimators=12, max_features='sqrt', random_state=42, n_jobs=1)
                ns['CV_FOLDS'] = 3
                ns['SHAP_BACKGROUND_SIZE'] = 8
                ns['plt'].show = lambda *args, **kwargs: None
                rng = np.random.default_rng(421)
                rows, cluster_rows, lst_rows = [], [], []
                for i in range(160):
                    grid_id = str(93175000687 + i)
                    geometry = box(106.7+(i % 16)*.009, -6.3+(i // 16)*.009,
                                   106.708+(i % 16)*.009, -6.292+(i // 16)*.009)
                    cluster = i % 4
                    cluster_rows.append({'grid_id': grid_id, 'k-means_cluster': cluster, 'geometry': geometry})
                    baseline = 31 + cluster*.7 + rng.normal(0, .4)
                    lst = {'grid_id': grid_id}
                    for year in ns['LAG_YEARS']:
                        lst[f'lst_{year}'] = baseline + rng.normal(0, .3)
                    last_ndvi = last_ndbi = None
                    for year in ns['INDEX_YEARS']:
                        ndvi = rng.uniform(.1, .6)
                        ndbi = rng.uniform(-.15, .3)
                        last_ndvi, last_ndbi = ndvi, ndbi
                        is_l7 = year < 2013
                        passed = not (i == 0 and year == 2012)
                        rows.append(dict(grid_id=grid_id, year=year, sensor='landsat7' if is_l7 else 'landsat8',
                            NDVI=ndvi if passed else None, NDBI=ndbi if passed else None,
                            NDVI_raw=ndvi-.005 if is_l7 else ndvi, NDBI_raw=ndbi+.002 if is_l7 else ndbi,
                            valid_fraction=.95 if passed else .4, n_valid_pixels=1000 if passed else 400,
                            obs_mean=4, scene_count_aoi=10, unique_days_aoi=8, quality_ok=int(passed),
                            min_observations=2, min_valid_fraction=.8, analysis_scale_m=30,
                            analysis_crs='EPSG:32748', schema_version='landsat_oli_v2',
                            harmonization='Roy2016_Table2_SR_RMA_ETM_to_OLI' if is_l7 else 'OLI_reference',
                            local_validation='synthetic_fixture_not_research', start_date=f'{year}-06-01',
                            end_date_exclusive=f'{year}-10-01', geometry=geometry))
                    lst['lst_2024_EXCLUDED'] = baseline - 2*last_ndvi + 3*last_ndbi + rng.normal(0, .1)
                    if i == 1:
                        lst['lst_2024_EXCLUDED'] = None
                    lst_rows.append(lst)
                cls.synthetic_indices = gpd.GeoDataFrame(rows, crs='EPSG:4326')
                ns['PATH_NDVI_NDBI'].parent.mkdir(parents=True, exist_ok=True)
                cls.synthetic_indices.to_file(ns['PATH_NDVI_NDBI'], driver='GeoJSON')
                gpd.GeoDataFrame(cluster_rows, crs='EPSG:4326').to_file(ns['PATH_CLUSTER'], driver='GeoJSON')
                ns['PATH_LST'] = cls.directory / 'data/cluster_results_k4.csv'
                pd.DataFrame(lst_rows).to_csv(ns['PATH_LST'], index=False)
                for cell in notebook.cells:
                    if cell.cell_type != 'code' or cell.id in ['setup', 'config']:
                        continue
                    print('RUN', cell.id, flush=True)
                    exec(cell.source, ns)
        except Exception:
            log_path = cls.directory / 'execution.log'
            if log_path.exists():
                print(log_path.read_text(encoding='utf-8')[-6000:].encode('ascii', 'replace').decode())
            raise
        finally:
            os.chdir(old_cwd)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_2024_predictors_and_train_only_scaler(self):
        import numpy as np
        ns = self.ns
        for key in ['M3_LagAll', 'M4_LagAll_byCluster']:
            config = ns['MODEL_CONFIGS'][key]
            self.assertEqual(len(config['features']), 17)
            self.assertIn('ndvi2024', config['features'])
            self.assertIn('ndbi2024', config['features'])
            self.assertNotIn('lst_2024', config['features'])
            result = ns['all_results'][(key, 'SVR')]
            for cluster, model in result['models'].items():
                frame = ns['df'].iloc[ns['train_indices']]
                if cluster != 'global':
                    frame = frame[frame[ns['CLUSTER_COL']].eq(cluster)]
                np.testing.assert_allclose(model.named_steps['scaler'].mean_, frame[config['features']].mean().to_numpy())

    def test_qa_exclusion_and_holdout_alignment(self):
        import numpy as np
        ns = self.ns
        self.assertEqual(len(ns['df']), 158)
        self.assertEqual(len(ns['df_summary']), 8)
        for train, validation in ns['cv_folds']:
            self.assertFalse(np.intersect1d(train, ns['test_indices']).size)
            self.assertFalse(np.intersect1d(validation, ns['test_indices']).size)
            self.assertFalse(np.intersect1d(train, validation).size)
        for result in ns['all_results'].values():
            np.testing.assert_array_equal(result['test_indices'], ns['test_indices'])
        self.assertEqual(len(ns['sensitivity_rows']), 4)
        self.assertTrue((ns['OUTPUT_DIR'] / 'all_predictions_test_set.csv').exists())
        for algorithm, key in ns['best_keys'].items():
            selected = ns['df_summary'][ns['df_summary']['Algorithm'].eq(algorithm)].sort_values(['CV_RMSE_Mean', 'ConfigKey']).iloc[0]
            self.assertEqual(key, selected['ConfigKey'])

    def test_group_shap_known_linear_solution(self):
        import numpy as np
        X = np.array([[1., 3., 5.], [2., -1., 4.]])
        background = np.array([[0., 1., 2.], [2., 3., 4.]])
        weights = np.array([2., 3., -1.])
        predict = lambda x: x @ weights + 5
        phi, base, prediction = self.ns['exact_group_shap'](predict, X, background, {'A': [0, 1], 'B': [2]})
        centered = (X-background.mean(axis=0))*weights
        np.testing.assert_allclose(phi[:, 0], centered[:, :2].sum(axis=1))
        np.testing.assert_allclose(phi[:, 1], centered[:, 2])
        np.testing.assert_allclose(base+phi.sum(axis=1), prediction)
        for row in self.ns['shap_verification_rows']:
            self.assertLess(row['feature_max_error'], 1e-4)
            self.assertLess(row['group_max_error'], 1e-6)

    def test_invalid_inputs_fail_explicitly(self):
        import pandas as pd
        import geopandas as gpd
        original = self.synthetic_indices
        cases = [
            original.assign(schema_version='old_data'),
            original.assign(sensor='sentinel2'),
            original.assign(valid_fraction=1.5),
            original.assign(min_observations=0),
            original[original['year'].ne(2024)],
            gpd.GeoDataFrame(pd.concat([original, original.iloc[:1]], ignore_index=True), crs=original.crs),
        ]
        for i, frame in enumerate(cases):
            path = self.directory / f'invalid_{i}.geojson'
            frame.to_file(path, driver='GeoJSON')
            with self.subTest(case=i), self.assertRaises(ValueError):
                self.ns['load_indices'](path)
        with self.assertRaises(FileNotFoundError):
            self.ns['load_indices'](self.directory / 'not_exported.geojson')

    def test_lst_long_format_supported(self):
        import geopandas as gpd
        import numpy as np
        rows = []
        for _, row in self.ns['df'].iterrows():
            geometry = self.synthetic_indices.loc[self.synthetic_indices['grid_id'].eq(row['grid_id']), 'geometry'].iloc[0]
            for year in self.ns['INDEX_YEARS']:
                rows.append(dict(grid_id=row['grid_id'], period=year, mean=row[f'lst_{year}'], geometry=geometry))
        path = self.directory / 'lst_long.geojson'
        gpd.GeoDataFrame(rows, crs='EPSG:4326').to_file(path, driver='GeoJSON')
        loaded = self.ns['load_lst'](path).set_index('grid_id')
        expected = self.ns['df'].set_index('grid_id')
        for year in self.ns['INDEX_YEARS']:
            np.testing.assert_allclose(loaded.loc[expected.index, f'lst_{year}'], expected[f'lst_{year}'])

    def test_missing_cluster_is_audited_and_empty_period_explained(self):
        import geopandas as gpd
        ns = self.ns
        clusters = gpd.read_file(ns['PATH_CLUSTER'])
        missing_id = ns['df']['grid_id'].iloc[0]
        subset = clusters[clusters['grid_id'].ne(missing_id)]
        path = self.directory / 'cluster_subset.geojson'
        subset.to_file(path, driver='GeoJSON')
        frame, _, audit = ns['prepare_data'](ns['panel'], path, ns['PATH_LST'])
        self.assertEqual(len(frame), 157)
        excluded = audit[audit['grid_id'].eq(missing_id)].iloc[0]
        self.assertFalse(excluded['included'])
        self.assertIn('kmeans_cluster', excluded['missing_columns'])
        empty = ns['panel'].copy()
        mask = empty['year'].eq(2009)
        empty.loc[mask, 'usable'] = False
        empty.loc[mask, ['NDVI', 'NDBI', 'NDVI_raw', 'NDBI_raw']] = float('nan')
        with self.assertRaisesRegex(ValueError, r'periode \[2009\]'):
            ns['prepare_data'](empty, ns['PATH_CLUSTER'], ns['PATH_LST'])

    def test_single_observation_keeps_coverage_and_null_checks(self):
        frame = self.synthetic_indices.copy()
        frame['min_observations'] = 1
        frame['unique_days_aoi'] = 1
        frame['obs_mean'] = .95
        # Nilai tidak boleh dibuat kembali walaupun quality_ok sempat bernilai 1.
        frame.loc[0, ['NDVI', 'NDBI']] = float('nan')
        frame.loc[1, 'valid_fraction'] = .79
        path = self.directory / 'single_observation.geojson'
        frame.to_file(path, driver='GeoJSON')
        loaded = self.ns['load_indices'](path)
        self.assertTrue(loaded['usable'].any())
        self.assertTrue(loaded.loc[loaded['valid_fraction'].lt(.8), 'usable'].eq(False).all())
        row = loaded[loaded['grid_id'].eq(frame.loc[0, 'grid_id']) & loaded['year'].eq(frame.loc[0, 'year'])].iloc[0]
        self.assertFalse(row['usable'])
        self.assertTrue(self.ns['pd'].isna(row['NDVI']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
