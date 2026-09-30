// ======================================================
// GRID 1 KM & NDVI–NDBI MULTI-TAHUN DKI JAKARTA (FIXED)
// Perbaikan: masking awan per-piksel (S2/L7/L8) + fallback
// komposit lebih panjang agar tidak ada grid yang NULL.
// ======================================================

// 1. LOAD SHAPEFILE DKI JAKARTA
var jakarta = ee.FeatureCollection(
  "projects/skripsi-pendahuluan/assets/jakarta",
);
Map.centerObject(jakarta, 10);
Map.addLayer(jakarta, {}, "Jakarta Boundary");

// ======================================================
// 2. GRID 1x1 KM (sama seperti sebelumnya)
// ======================================================
var proj = ee.Projection("EPSG:32748").atScale(1000);
var coords = ee.Image.pixelCoordinates(proj);

var gridId = coords
  .select("x")
  .add(coords.select("y").multiply(1e7))
  .floor()
  .toInt64()
  .rename("grid_id");

var dummy = ee.Image.constant(1).rename("dummy");
var gridImage = gridId.addBands(dummy);

var grid = gridImage.reduceToVectors({
  geometry: jakarta.geometry(),
  scale: 1000,
  geometryType: "polygon",
  reducer: ee.Reducer.first(),
  labelProperty: "grid_id",
  maxPixels: 1e13,
});

print("Jumlah grid 1 km:", grid.size());

// ======================================================
// 3A. LANDSAT 7 ETM+ dengan cloud mask (QA_PIXEL)
// ======================================================
function maskL7(img) {
  var qa = img.select("QA_PIXEL");
  var cloud = qa
    .bitwiseAnd(1 << 3)
    .eq(0) // cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0)) // cloud shadow
    .and(qa.bitwiseAnd(1 << 1).eq(0)); // dilated cloud
  return img.updateMask(cloud);
}

function getNDVI_NDBI_Landsat7(year) {
  var start = year + "-06-01";
  var end = year + "-09-30"; // window diperlebar

  var col = ee
    .ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filterDate(start, end)
    .filterBounds(jakarta)
    .filter(ee.Filter.lt("CLOUD_COVER", 50)) // longgarkan filter scene
    .map(maskL7)
    .map(function (img) {
      var optical = img
        .select(["SR_B3", "SR_B4", "SR_B5"])
        .multiply(0.0000275)
        .add(-0.2);
      var ndvi = optical
        .normalizedDifference(["SR_B4", "SR_B3"])
        .rename("NDVI");
      var ndbi = optical
        .normalizedDifference(["SR_B5", "SR_B4"])
        .rename("NDBI");
      return ndvi.addBands(ndbi);
    });

  print("L7 " + year + " scene count:", col.size());
  var median = col.median();
  var mosaic = col.mosaic(); // fallback isi celah
  return median.unmask(mosaic).clip(jakarta);
}

// ======================================================
// 3B. LANDSAT 8 OLI dengan cloud mask
// ======================================================
function maskL8(img) {
  var qa = img.select("QA_PIXEL");
  var cloud = qa
    .bitwiseAnd(1 << 3)
    .eq(0)
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 1).eq(0));
  return img.updateMask(cloud);
}

function getNDVI_NDBI_Landsat8(year) {
  var start = year + "-06-01";
  var end = year + "-09-30";

  var col = ee
    .ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterDate(start, end)
    .filterBounds(jakarta)
    .filter(ee.Filter.lt("CLOUD_COVER", 50))
    .map(maskL8)
    .map(function (img) {
      var optical = img
        .select(["SR_B4", "SR_B5", "SR_B6"])
        .multiply(0.0000275)
        .add(-0.2);
      var ndvi = optical
        .normalizedDifference(["SR_B5", "SR_B4"])
        .rename("NDVI");
      var ndbi = optical
        .normalizedDifference(["SR_B6", "SR_B5"])
        .rename("NDBI");
      return ndvi.addBands(ndbi);
    });

  print("L8 " + year + " scene count:", col.size());
  var median = col.median();
  var mosaic = col.mosaic();
  return median.unmask(mosaic).clip(jakarta);
}

// ======================================================
// 3C. SENTINEL-2 SR HARMONIZED dengan cloud mask (SCL)
// ======================================================
function maskS2(img) {
  var scl = img.select("SCL");
  // buang: 3 cloud shadow, 8 cloud medium, 9 cloud high, 10 cirrus
  var mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
  return img.updateMask(mask);
}

function getNDVI_NDBI_Sentinel2(year) {
  var start = year + "-06-01";
  var end = year + "-09-30"; // window diperlebar dari 2 bulan jadi 4 bulan

  var col = ee
    .ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate(start, end)
    .filterBounds(jakarta)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40)) // longgarkan filter scene
    .map(maskS2)
    .map(function (img) {
      var ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI");
      var ndbi = img.normalizedDifference(["B11", "B8"]).rename("NDBI");
      return ndvi.addBands(ndbi);
    });

  print("S2 " + year + " scene count:", col.size());

  var median = col.median(); // lebih tahan outlier dibanding mean
  var mosaic = col.mosaic(); // isi celah dari median yang masih null
  return median.unmask(mosaic).clip(jakarta);
}

// ======================================================
// 4. KONFIGURASI TAHUN & SENSOR
// ======================================================
var yearConfig = [
  { year: "2009", sensor: "landsat7" },
  { year: "2012", sensor: "landsat7" },
  { year: "2015", sensor: "landsat8" },
  { year: "2018", sensor: "landsat8" }, // S2 SR belum reliable di Jakarta pada 2018
  { year: "2021", sensor: "sentinel2" },
  { year: "2024", sensor: "sentinel2" },
];

// ======================================================
// 5. PROSES TIAP TAHUN — REDUCE (mean + count piksel valid)
// ======================================================

// Reducer gabungan: mean (nilai NDVI/NDBI) + count (jumlah piksel
// valid yang dipakai menghitung mean tsb, indikator kualitas komposit)
var meanCountReducer = ee.Reducer.mean().combine({
  reducer2: ee.Reducer.count(),
  sharedInputs: true,
});

var allYearResults = []; // menampung FeatureCollection tiap tahun

yearConfig.forEach(function (cfg) {
  var img;
  if (cfg.sensor === "landsat7") {
    img = getNDVI_NDBI_Landsat7(cfg.year);
  } else if (cfg.sensor === "landsat8") {
    img = getNDVI_NDBI_Landsat8(cfg.year);
  } else {
    img = getNDVI_NDBI_Sentinel2(cfg.year);
  }

  Map.addLayer(
    img.select("NDVI"),
    { min: -0.2, max: 0.8, palette: ["red", "white", "darkgreen"] },
    "NDVI " + cfg.year,
  );

  var result = img
    .select(["NDVI", "NDBI"])
    .reduceRegions({
      collection: grid,
      reducer: meanCountReducer,
      scale: 1000,
      tileScale: 4, // hindari timeout/error saat area besar
    })
    .map(function (f) {
      return f
        .set({
          NDVI: f.get("NDVI_mean"), // reducer gabungan menamai output <band>_mean
          NDBI: f.get("NDBI_mean"), // bukan 'NDVI'/'NDBI' polos
          count: f.get("NDVI_count"), // jumlah piksel valid (NDVI & NDBI sama krn sharedInputs)
          year: cfg.year,
          sensor: cfg.sensor,
        })
        .select(["grid_id", "NDVI", "NDBI", "count", "year", "sensor"]);
    });

  // Cek berapa fitur yang masih NULL setelah perbaikan
  var nullCount = result.filter(ee.Filter.eq("NDVI", null)).size();
  print("Grid NULL tersisa di " + cfg.year + ":", nullCount);
  print("Total baris " + cfg.year + ":", result.size());

  allYearResults.push(result);
});

// ======================================================
// 6. GABUNGKAN SEMUA TAHUN & EKSPOR SEKALI JADI SATU FILE
// ======================================================
var merged = ee.FeatureCollection(allYearResults).flatten();
print("Total baris gabungan semua tahun:", merged.size());

Export.table.toDrive({
  collection: merged,
  description: "FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS",
  fileNamePrefix: "FINAL_NDVI_NDBI_Grid1km_Jakarta_ALL_YEARS",
  fileFormat: "GeoJSON",
});
