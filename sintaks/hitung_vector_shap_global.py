"""True Vector SHAP M3 RF global: koalisi eksak LST, NDVI, NDBI."""
from pathlib import Path
import json
from math import factorial
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

OUTPUT = Path(__file__).resolve().parents[1] / 'data/output/regression_legacy'


def main():
    frame = pd.read_csv(OUTPUT / 'analysis_data.csv', dtype={'grid_id': str}, float_precision='round_trip')
    features = [f'lst_{year}' for year in [2009, 2012, 2015, 2018, 2021]]
    features += [f'{var}{year}' for var in ['ndvi', 'ndbi'] for year in [2009, 2012, 2015, 2018, 2021, 2024]]
    train, test = train_test_split(np.arange(len(frame)), test_size=.2, random_state=42)
    model = RandomForestRegressor(n_estimators=300, max_features='sqrt', random_state=42, n_jobs=-1)
    model.fit(frame.loc[train, features].to_numpy(), frame.loc[train, 'lst_2024'])
    x = frame.loc[test, features].to_numpy()
    predicted = model.predict(x)
    reference = pd.read_csv(OUTPUT / 'all_predictions_test_set.csv', dtype={'grid_id': str}, float_precision='round_trip').set_index('grid_id')
    column = next(c for c in reference if 'M3_LagAll_RF' in c)
    np.testing.assert_allclose(predicted, reference.loc[frame.loc[test, 'grid_id'], column], atol=1e-9)
    # Same reference convention as the last archived notebook cell: mean of test features.
    baseline = float(model.predict(x.mean(axis=0, keepdims=True))[0])
    names = ['LST', 'NDVI', 'NDBI']
    groups = [[i for i, f in enumerate(features) if f.upper().startswith(name)] for name in names]
    values = {}
    for mask in range(8):
        masked = np.tile(x.mean(axis=0), (len(x), 1))
        for j, indices in enumerate(groups):
            if mask & (1 << j):
                masked[:, indices] = x[:, indices]
        values[mask] = model.predict(masked)
    phi = np.zeros((len(x), 3))
    for j in range(3):
        for mask in range(8):
            if not mask & (1 << j):
                size = mask.bit_count()
                weight = factorial(size) * factorial(2-size) / factorial(3)
                phi[:, j] += weight * (values[mask | (1 << j)] - values[mask])
    np.testing.assert_allclose(baseline + phi.sum(axis=1), predicted, atol=1e-12)
    absolute = np.abs(phi)
    pd.DataFrame({'grid_id': frame.loc[test, 'grid_id'].to_numpy(), 'prediction': predicted,
                  'baseline': baseline, **{f'phi_{name}': phi[:, j] for j, name in enumerate(names)}}).to_csv(OUTPUT / 'true_vector_shap_global_M3_RF.csv', index=False)
    stats = [dict(variable=name, mean=float(absolute[:,j].mean()), std=float(absolute[:,j].std()),
        q25=float(np.quantile(absolute[:,j],.25)), median=float(np.median(absolute[:,j])),
        q75=float(np.quantile(absolute[:,j],.75)),
        contribution_pct=float(absolute[:,j].mean()/absolute.mean(axis=0).sum()*100)) for j,name in enumerate(names)]
    summary = dict(model='M3_RF', description='M3 Random Forest tanpa klaster: LST + NDVI + NDBI',
        source='regression_legacy run ulang', variables=stats, n_samples=len(test), baseline=baseline,
        background='mean X_test, mengikuti sel terakhir notebook arsip',
        local_accuracy_error=float(np.max(np.abs(baseline+phi.sum(axis=1)-predicted))))
    (OUTPUT / 'true_vector_shap_global_M3_RF.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

