"""Audit metadata scene Landsat di katalog publik; bukan audit piksel bebas awan."""
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]


def query(year):
    # Bounding box seluruh geometri grid sumber, termasuk grid pesisir.
    source = ROOT.parent / 'data/FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS.geojson'
    from shapely.geometry import shape
    geometries = [shape(f['geometry']) for f in json.loads(source.read_text())['features']]
    bounds = [g.bounds for g in geometries]
    bbox = [min(b[0] for b in bounds), min(b[1] for b in bounds),
            max(b[2] for b in bounds), max(b[3] for b in bounds)]
    params = {'collections': 'landsat-c2-l2', 'bbox': ','.join(map(str, bbox)),
              'datetime': f'{year}-06-01T00:00:00Z/{year}-09-30T23:59:59Z', 'limit': 100}
    url = 'https://planetarycomputer.microsoft.com/api/stac/v1/search?' + urlencode(params)
    rows = []
    while url:
        with urlopen(url, timeout=60) as response:
            data = json.load(response)
        for f in data['features']:
            p = f['properties']
            rows.append({'year': year, 'id': f['id'], 'platform': p.get('platform'),
                         'datetime': p.get('datetime'), 'cloud_cover_scene': p.get('eo:cloud_cover'),
                         'category': p.get('landsat:collection_category'),
                         'wrs_path': p.get('landsat:wrs_path'), 'wrs_row': p.get('landsat:wrs_row'),
                         'bbox_query': json.dumps(bbox)})
        url = next((l['href'] for l in data.get('links', []) if l['rel'] == 'next'), None)
    return rows


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = [r for result in pool.map(query, YEARS) for r in result]
    if not rows:
        raise RuntimeError('Katalog tidak mengembalikan scene.')
    output = ROOT / 'audit_katalog_landsat.csv'
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for year in YEARS:
        sensor = 'landsat-7' if year < 2013 else 'landsat-8'
        subset = [r for r in rows if r['year'] == year and r['platform'] == sensor and r['category'] == 'T1']
        filtered = [r for r in subset if r['cloud_cover_scene'] is not None and r['cloud_cover_scene'] < 50]
        dates = sorted({r['datetime'][:10] for r in filtered})
        print(year, sensor, 'T1:', len(subset), 'cloud<50:', len(filtered), 'dates:', ','.join(dates))
    print('Metadata tersimpan:', output)
