# NIDO · Visualizador espacial del Índice de Desarrollo Infantil

Aplicación web interactiva que explora el **Índice NIDO** sobre ~66.500 radios censales de Argentina. Permite ajustar la ponderación de 4 dimensiones (salud, educación, contexto socioeconómico, ambiente) y visualizar el impacto en la distribución espacial del índice en tiempo real, con un Web Worker que mantiene la UI fluida.

**Stack:** Svelte 5, MapLibre GL JS 5, PMTiles, Vite 8, Web Worker, Railway.

## Desarrollo local

```bash
npm install
npm run dev                   # servidor en http://localhost:5173
npm run build                 # build de producción en dist/
npm run preview               # previsualizar build local
```

Para regenerar los datos (requiere Python + tippecanoe):

```bash
source .venv/bin/activate
python3 scripts/prepare_data.py
```

## Pipeline de datos

`scripts/prepare_data.py` lee `data/indicadores.gpkg` (112 MB, no trackeado en git, descargado en build desde GitHub Releases) y genera en `public/data/`:

| Archivo | Formato | Contenido |
|---------|---------|-----------|
| `nido.pmtiles` | PMTiles | Tiles vectoriales (zooms 3–12, ~80 MB) |
| `dims.bin` | Float32Array | Valores de las 4 dimensiones por radio censal |
| `provinces.json` | JSON | Lista de provincias |
| `province_bounds.json` | JSON | Bounds por provincia |
| `provincias.geojson` | GeoJSON | Límites provinciales disueltos |

Dependencias: `tippecanoe`, `pmtiles` CLI, Python con `geopandas` + `numpy`.

## Arquitectura

```
src/
├── main.js                  # entry point
├── app.css                  # variables CSS, Manrope, reset
├── App.svelte               # orquestación: carga datos, Worker, sidebar drawer responsive
└── lib/
    ├── Map.svelte           # MapLibre GL + PMTiles + labels (OpenFreeMap) + hover highlight
    │                        # + popup con color de categoría + geocoder Nominatim + pin de búsqueda
    ├── Sidebar.svelte       # panel lateral: selector de provincia, pesos por dimensión, logo FRACTAL
    ├── Legend.svelte        # leyenda de colores invertida
    ├── store.svelte.js      # estado reactivo ($state runes)
    └── nido.worker.js       # Web Worker: NIDO computation fuera del hilo principal
```

### Funcionalidades clave

- **Cálculo en Web Worker:** las 4 dimensiones se ponderan, normalizan y categorizan (5 quintiles) en un worker, evitando bloqueos de UI.
- **Feature states:** los colores se aplican vía `map.setFeatureState()`, permitiendo hover highlight individual sin recargar datos.
- **Geocoder:** búsqueda de direcciones con Nominatim (restringido a Argentina), pin sutil al seleccionar, marcador removible al clicar el mapa.
- **OpenMapTiles labels:** capas de nombres de lugar filtradas al polígono de Argentina, con jerarquía (suburb → town → city → state → country).
- **Responsive:** sidebar se transforma en drawer (85vw, backdrop, transición cubic-bezier) en mobile. Edge peek de color brand como indicador visual.
- **Tipografía:** Manrope (Google Fonts), 400–800.

## Deploy (Railway)

Automático vía `railway.json`. El build:

1. Instala `tippecanoe` + `python3-pip`
2. `npm ci` + `npm install -g pmtiles`
3. Descarga `data/indicadores.gpkg` desde GitHub Releases (o variable `GPKG_URL`)
4. `pip install -r requirements.txt`
5. `python3 scripts/prepare_data.py` → genera `public/data/`
6. `npm run build` → genera `dist/`
7. Sirve con `serve dist`

Sin CLI necesario: conectar repo desde railway.app y deployar.

## Brand

- Colores: `#002d83`, `#005cb7`, `#006cc6`
- Logo FRACTAL en sidebar footer

## Licencia

Datos: procesamiento propio sobre datos censales INDEC y registros administrativos.
Código: GPL v3.
