import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
PUBLIC_DATA_DIR = Path(__file__).resolve().parent.parent / 'public' / 'data'

PMTILES_BIN = shutil.which('pmtiles', path='/usr/local/bin:/usr/bin:/bin') or 'pmtiles'

VARIABLES = {
    'salud': ['cobertura_salud', 'cercania_a_salud'],
    'educacion': ['asiste_educ_0_5', 'cercania_a_j_maternal', 'cercania_a_j_infantes'],
    'contexto': ['clima_educ_alto_muy_alto', 'tasa_pob_activa_empleada', 'tasa_empleados_sectores_sec_ter'],
    'ambiente': ['cercania_a_EV'],
}


def main():
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\U0001f4c2 Leyendo GeoPackage...")
    gdf = gpd.read_file(DATA_DIR / 'indicadores.gpkg')
    gdf = gdf.to_crs(epsg=4326)
    gdf['geometry'] = gdf.geometry.buffer(0)

    print(f"\u2705 {len(gdf)} features cargados")

    # --- Dimension averages ---
    print("\U0001f4ca Calculando promedios por dimensi\u00f3n...")
    dims_list = []
    for dim, cols in VARIABLES.items():
        available = [c for c in cols if c in gdf.columns]
        dims_list.append(gdf[available].mean(axis=1).values)

    dims_array = np.column_stack(dims_list).astype(np.float32)

    print(f"\u24fe Escribiendo dims.bin ({dims_array.nbytes / 1e6:.1f} MB)...")
    with open(PUBLIC_DATA_DIR / 'dims.bin', 'wb') as f:
        f.write(dims_array.tobytes())

    # --- Province list ---
    print("\U0001f5fa\ufe0f Generando provincias...")
    provinces = sorted(gdf['NOMPROV'].unique().tolist())
    with open(PUBLIC_DATA_DIR / 'provinces.json', 'w') as f:
        json.dump(provinces, f)

    # --- Province bounds ---
    print("\U0001f5fa\ufe0f Calculando bounds por provincia...")
    bounds = {}
    for prov in provinces:
        subset = gdf[gdf['NOMPROV'] == prov]
        b = subset.total_bounds
        bounds[prov] = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]

    with open(PUBLIC_DATA_DIR / 'province_bounds.json', 'w') as f:
        json.dump(bounds, f)

    # --- Province boundaries (dissolved) ---
    print("\U0001f5fa\ufe0f Generando l\u00edmites provinciales...")
    provincias = gdf.dissolve(by='NOMPROV').reset_index()[['NOMPROV', 'geometry']]
    with open(PUBLIC_DATA_DIR / 'provincias.geojson', 'w') as f:
        f.write(provincias.to_json())

    # --- MBTiles v\u00eda tippecanoe + convert a PMTiles ---
    print("\U0001f3d7\ufe0f Creando GeoJSON temporal para tiles...")
    gdf_simple = gdf[[
        'NOMPROV', 'NOMDEPTO',
        'cobertura_salud', 'asiste_educ_0_5',
        'clima_educ_alto_muy_alto', 'tasa_pob_activa_empleada',
        'tasa_empleados_sectores_sec_ter', 'tasa_sin_privaciones',
        'cercania_a_salud', 'cercania_a_j_maternal',
        'cercania_a_j_infantes', 'cercania_a_EV', 'geometry'
    ]].copy()
    gdf_simple['id'] = range(len(gdf_simple))

    geojson_path = PUBLIC_DATA_DIR / 'features_for_tiles.geojson'
    with open(geojson_path, 'w') as f:
        f.write(gdf_simple.to_json())

    mbtiles_path = PUBLIC_DATA_DIR / 'nido_temp.mbtiles'
    if mbtiles_path.exists():
        mbtiles_path.unlink()

    print("\U0001f3d7\ufe0f Ejecutando tippecanoe (esto puede tomar unos minutos)...")
    result = subprocess.run([
        'tippecanoe',
        '-o', str(mbtiles_path),
        '-Z3', '-z12',
        '-l', 'nido',
        '--no-tiny-polygon-reduction',
        '--drop-densest-as-needed',
        '--no-tile-size-limit',
        str(geojson_path),
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"\u274c tippecanoe error:\n{result.stderr}")
        mbtiles_path.unlink(missing_ok=True)
        geojson_path.unlink()
        return

    mbtiles_size = mbtiles_path.stat().st_size / 1e6
    print(f"   MBTiles: {mbtiles_size:.1f} MB")

    pmtiles_path = PUBLIC_DATA_DIR / 'nido.pmtiles'
    if pmtiles_path.exists():
        pmtiles_path.unlink()

    print("\U0001f504 Convirtiendo MBTiles a PMTiles...")
    result2 = subprocess.run([
        PMTILES_BIN, 'convert',
        str(mbtiles_path),
        str(pmtiles_path),
    ], capture_output=True, text=True)

    mbtiles_path.unlink()

    if result2.returncode != 0:
        print(f"\u274c pmtiles convert error:\n{result2.stderr}")
        geojson_path.unlink()
        return

    print(f"\u2705 PMTiles creado: {pmtiles_path}")
    pmtiles_size = pmtiles_path.stat().st_size / 1e6
    print(f"   Tama\u00f1o: {pmtiles_size:.1f} MB")

    warnings = [l for l in result.stderr.split('\n') if 'Warning' in l]
    for w in warnings:
        print(f"   \u26a0\ufe0f {w}")

    geojson_path.unlink()

    print("\n\u2728 \u00a1Datos preparados!")


if __name__ == '__main__':
    main()
