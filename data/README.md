# Data directory

Large datasets, downloaded satellite imagery, intermediate rasters, and generated geospatial products are intentionally excluded from Git.

Expected future layout:

- aoi/ — small study-area GeoJSON files.
- raw/ — downloaded source data.
- processed/ — normalized/derived data.
- external/ — independent validation data.

Do not commit large datasets or credentials.

Phase 1 does not require any data download.
