// Jalankan di Earth Engine Code Editor, lalu Run kedua Tasks ekspor.
// Grid 1 km, statistik piksel 30 m; Landsat 7 (2009/2012), Landsat 8 (2015-2024).
// Roy et al. 2016 Table 2 SURFACE REFLECTANCE, RMA ETM+ -> OLI:
// https://pmc.ncbi.nlm.nih.gov/articles/PMC6999663/
// Koefisien dari CONUS/produk generasi lama: belum divalidasi lokal di Jakarta.
// Pembanding raw memakai mask sama. Penyesuaian ini bukan z-score atau HLS.
var CFG = {
  jakartaAsset: 'projects/skripsi-pendahuluan/assets/jakarta',
  gridAsset: '', // isi asset grid penelitian jika tersedia
  years: [2009, 2012, 2015, 2018, 2021, 2024],
  crs: 'EPSG:32748', transform: [30, 0, 0, 0, -30, 0],
  // Dua scene 2009 tidak berarti setiap piksel terlihat pada dua tanggal.
  // Pakai seluruh piksel yang memiliki >=1 pengamatan valid; cakupan >=80% tetap wajib.
  // Laporkan juga dukungan >=2 pengamatan untuk menilai kekuatan komposit temporal.
  minObservations: 1, minValidFraction: 0.80,
  maxSceneCloud: 50, exportFolder: 'NDVI_NDBI_Jakarta_v2',
  exportName: 'NDVI_NDBI_Grid1km_Jakarta_Landsat_OLIref_v2'
};
var jakarta = ee.FeatureCollection(CFG.jakartaAsset);
var aoi = jakarta.geometry();
var analysisProj = ee.Projection(CFG.crs, CFG.transform);
Map.centerObject(jakarta, 10);
var grid;
if (CFG.gridAsset) {
  grid = ee.FeatureCollection(CFG.gridAsset);
} else {
  // Rumus identitas grid sama dengan skrip asli.
  var gridProj = ee.Projection(CFG.crs).atScale(1000);
  var coords = ee.Image.pixelCoordinates(gridProj);
  var ids = coords.select('x').add(coords.select('y').multiply(1e7))
    .floor().toInt64().rename('grid_id');
  grid = ids.addBands(ee.Image.constant(1).rename('dummy')).reduceToVectors({
    geometry: aoi, crs: gridProj, scale: 1000, geometryType: 'polygon',
    reducer: ee.Reducer.first(), labelProperty: 'grid_id', maxPixels: 1e13
  });
}
grid = grid.map(function(f) {
  return f.set('grid_id', ee.Number.parse(ee.String(f.get('grid_id'))).format('%.0f'));
});
print('Grid (cek kesamaan dengan LST/cluster)', grid.size());

function indices(sr, suffix) {
  var red = sr.select('red'), nir = sr.select('nir'), swir = sr.select('swir1');
  var valid = sr.gte(0).and(sr.lte(1)).reduce(ee.Reducer.min())
    .and(nir.add(red).gt(1e-6)).and(swir.add(nir).gt(1e-6));
  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI' + suffix);
  var ndbi = swir.subtract(nir).divide(swir.add(nir)).rename('NDBI' + suffix);
  return ndvi.addBands(ndbi).updateMask(valid);
}
function prepare(img, isL7) {
  var qa = img.select('QA_PIXEL');
  // fill, dilated cloud, cloud, shadow, snow; cirrus khusus OLI.
  var badBits = (1 << 0) | (1 << 1) | (1 << 3) | (1 << 4) | (1 << 5);
  if (!isL7) badBits = badBits | (1 << 2);
  var mask = qa.bitwiseAnd(badBits).eq(0).and(img.select('QA_RADSAT').eq(0));
  var bands = isL7 ? ['SR_B3', 'SR_B4', 'SR_B5'] : ['SR_B4', 'SR_B5', 'SR_B6'];
  var raw = img.select(bands, ['red', 'nir', 'swir1'])
    .multiply(0.0000275).add(-0.2).updateMask(mask);
  var adjusted = raw;
  if (isL7) {
    adjusted = raw.multiply(ee.Image.constant([0.9825, 1.0073, 1.0171]))
      .add(ee.Image.constant([-0.0022, -0.0021, -0.0030]));
  }
  var result = indices(adjusted, '').addBands(indices(raw, '_raw'));
  result = result.updateMask(result.mask().reduce(ee.Reducer.min()));
  // Sampling nearest-neighbour pada grid 30 m bersama, sebelum komposit.
  return result.toFloat().reproject(analysisProj).copyProperties(img, ['system:time_start'])
    .set('date', img.date().format('YYYY-MM-dd'));
}
var outputs = [], audits = [];
function numberOrZero(value) {
  return ee.Number(ee.Algorithms.If(ee.Algorithms.IsEqual(value, null), 0, value));
}
CFG.years.forEach(function(year) {
  var isL7 = year < 2013, sensor = isL7 ? 'landsat7' : 'landsat8';
  var start = ee.Date.fromYMD(year, 6, 1);
  var end = ee.Date.fromYMD(year, 10, 1); // eksklusif, termasuk 30 September
  var id = isL7 ? 'LANDSAT/LE07/C02/T1_L2' : 'LANDSAT/LC08/C02/T1_L2';
  var available = ee.ImageCollection(id).filterBounds(aoi).filterDate(start, end);
  var scenes = available.filter(ee.Filter.lt('CLOUD_COVER', CFG.maxSceneCloud));
  var prepared = scenes.map(function(img) { return prepare(img, isL7); });
  var dates = ee.List(prepared.aggregate_array('date')).distinct().sort();
  // Hindari menghitung overlap dua scene pada tanggal sama sebagai dua observasi.
  var daily = ee.ImageCollection.fromImages(dates.map(function(date) {
    return prepared.filter(ee.Filter.eq('date', date)).median()
      .setDefaultProjection(analysisProj).set('date', date);
  }));
  // Template sepenuhnya masked menjaga skema jika koleksi kosong.
  var empty = ee.Image.constant([0, 0, 0, 0])
    .rename(['NDVI', 'NDBI', 'NDVI_raw', 'NDBI_raw'])
    .toFloat().updateMask(ee.Image.constant(0)).setDefaultProjection(analysisProj);
  daily = daily.merge(ee.ImageCollection.fromImages([empty]));
  var obs = daily.select('NDVI').count().unmask(0, false).rename('obs')
    .setDefaultProjection(analysisProj).clip(aoi);
  var composite = daily.median().setDefaultProjection(analysisProj)
    .updateMask(obs.gte(CFG.minObservations)).clip(aoi);
  var valid = composite.mask().reduce(ee.Reducer.min()).unmask(0, false).clip(aoi);
  var area = ee.Image.pixelArea().rename('total_area').clip(aoi);
  var image = composite.addBands(obs).addBands(area)
    .addBands(area.multiply(valid).rename('valid_area'))
    .addBands(area.multiply(obs.gte(1)).rename('area_ge1'))
    .addBands(area.multiply(obs.gte(2)).rename('area_ge2'));
  // Reducer berbobot (mean/sum) diletakkan sebelum reducer tanpa bobot (count).
  var reducer = ee.Reducer.mean().combine({reducer2: ee.Reducer.sum(), sharedInputs: true})
    .combine({reducer2: ee.Reducer.count(), sharedInputs: true});
  var result = image.reduceRegions({collection: grid, reducer: reducer,
    crs: CFG.crs, crsTransform: CFG.transform, tileScale: 4
  }).map(function(f) {
    var total = numberOrZero(f.get('total_area_sum'));
    var fraction = numberOrZero(f.get('valid_area_sum')).divide(total.max(1));
    var fractionGe1 = numberOrZero(f.get('area_ge1_sum')).divide(total.max(1));
    var fractionGe2 = numberOrZero(f.get('area_ge2_sum')).divide(total.max(1));
    var good = total.gt(0).and(fraction.gte(CFG.minValidFraction))
      .and(numberOrZero(f.get('NDVI_count')).gt(0));
    return ee.Feature(f.geometry(), {
      grid_id: f.get('grid_id'), year: year, sensor: sensor,
      NDVI: ee.Algorithms.If(good, f.get('NDVI_mean'), null),
      NDBI: ee.Algorithms.If(good, f.get('NDBI_mean'), null),
      NDVI_raw: ee.Algorithms.If(good, f.get('NDVI_raw_mean'), null),
      NDBI_raw: ee.Algorithms.If(good, f.get('NDBI_raw_mean'), null),
      n_valid_pixels: numberOrZero(f.get('NDVI_count')), valid_fraction: fraction,
      valid_fraction_ge1: fractionGe1, valid_fraction_ge2: fractionGe2,
      single_obs_fraction: fractionGe1.subtract(fractionGe2).max(0),
      quality_ok_ge2: total.gt(0).and(fractionGe2.gte(CFG.minValidFraction)),
      processing_revision: 'obs_support_v3',
      obs_mean: f.get('obs_mean'), scene_count_aoi: scenes.size(),
      unique_days_aoi: dates.size(), quality_ok: ee.Number(good),
      min_observations: CFG.minObservations, min_valid_fraction: CFG.minValidFraction,
      start_date: start.format('YYYY-MM-dd'), end_date_exclusive: end.format('YYYY-MM-dd'),
      analysis_scale_m: 30, analysis_crs: CFG.crs, schema_version: 'landsat_oli_v2',
      harmonization: isL7 ? 'Roy2016_Table2_SR_RMA_ETM_to_OLI' : 'OLI_reference',
      local_validation: 'not_performed'
    });
  });
  var passed = result.filter(ee.Filter.eq('quality_ok', 1)).size();
  var audit = ee.Feature(null, {
    year: year, sensor: sensor, scene_count_catalog: available.size(),
    scene_count_filtered: scenes.size(), unique_days: dates.size(),
    n_grids: grid.size(), n_grids_pass: passed, n_grids_fail: grid.size().subtract(passed),
    min_observations: CFG.minObservations, min_valid_fraction: CFG.minValidFraction,
    n_grids_pass_ge2: result.filter(ee.Filter.eq('quality_ok_ge2', 1)).size(),
    mean_valid_fraction_ge1: result.aggregate_mean('valid_fraction_ge1'),
    mean_valid_fraction_ge2: result.aggregate_mean('valid_fraction_ge2'),
    mean_single_obs_fraction: result.aggregate_mean('single_obs_fraction'),
    min_valid_fraction_observed: result.aggregate_min('valid_fraction'),
    mean_valid_fraction: result.aggregate_mean('valid_fraction')
  });
  print('Audit ' + year, audit);
  Map.addLayer(composite.select('NDVI'), {min: -0.2, max: 0.8,
    palette: ['brown', 'white', 'darkgreen']}, 'NDVI ' + year, false);
  Map.addLayer(obs, {min: 0, max: 10}, 'Tanggal valid ' + year, false);
  outputs.push(result); audits.push(audit);
});
Export.table.toDrive({collection: ee.FeatureCollection(outputs).flatten(),
  folder: CFG.exportFolder, description: CFG.exportName,
  fileNamePrefix: CFG.exportName, fileFormat: 'GeoJSON'});
Export.table.toDrive({collection: ee.FeatureCollection(audits), folder: CFG.exportFolder,
  description: 'audit_cakupan_landsat_v2', fileNamePrefix: 'audit_cakupan_landsat_v2', fileFormat: 'CSV'});
print('Revisi obs_support_v3: ekspor ulang kedua Tasks dan ganti file lokal lama.');
print('Minimum tanggal per piksel:', CFG.minObservations,
  'Minimum cakupan grid:', CFG.minValidFraction);
print('Data tanpa observasi tetap kosong; tidak ada interpolasi antarperiode.');
