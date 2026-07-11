<script>
  import { onMount } from 'svelte'
  import maplibregl from 'maplibre-gl'
  import { Protocol } from 'pmtiles'
  import 'maplibre-gl/dist/maplibre-gl.css'
  import { categories, selectedProvince, provinceBounds, loading } from './store.svelte.js'

  let container
  let map
  let popup
  let searchMarker = null
  let hoveredId = null
  let searchQuery = $state('')
  let searchResults = $state([])
  let searchOpen = $state(false)
  let searchTimer

  const COLORS = ['#d53e4f', '#fc8d59', '#fee08b', '#99d594', '#3288bd']
  const CAT_LABELS = ['Muy bajo', 'Bajo', 'Medio', 'Alto', 'Muy alto']

  function quintile(v) {
    if (v == null) return '-'
    if (v <= 0.2) return 'Muy baja'
    if (v <= 0.4) return 'Baja'
    if (v <= 0.6) return 'Media'
    if (v <= 0.8) return 'Alta'
    return 'Muy alta'
  }

  onMount(() => {
    const protocol = new Protocol()
    maplibregl.addProtocol('pmtiles', (params, cb) => protocol.tile(params, cb))

    map = new maplibregl.Map({
      container,
      style: {
        version: 8,
        glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
        sources: {
          positron: {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
            ],
            tileSize: 256,
            attribution: '© CARTO, © OpenStreetMap'
          },
          nido: {
            type: 'vector',
            url: 'pmtiles:///data/nido.pmtiles',
            promoteId: 'id'
          },
          provincias: {
            type: 'geojson',
            data: '/data/provincias.geojson'
          },
          'omt-labels': {
            type: 'vector',
            url: 'https://tiles.openfreemap.org/planet',
            attribution: 'OpenMapTiles'
          }
        },
        layers: [
          { id: 'positron-base', type: 'raster', source: 'positron' },
          {
            id: 'nido-fill',
            type: 'fill',
            source: 'nido',
            'source-layer': 'nido',
            paint: {
              'fill-color': ['case',
                ['==', ['feature-state', 'cat'], 0], COLORS[0],
                ['==', ['feature-state', 'cat'], 1], COLORS[1],
                ['==', ['feature-state', 'cat'], 2], COLORS[2],
                ['==', ['feature-state', 'cat'], 3], COLORS[3],
                ['==', ['feature-state', 'cat'], 4], COLORS[4],
                '#e5e7eb'
              ],
              'fill-opacity': ['case',
                ['==', ['feature-state', 'hover'], true], 0.92,
                0.76
              ]
            }
          },
          {
            id: 'prov-outline',
            type: 'line',
            source: 'provincias',
            paint: {
              'line-color': '#ffffff',
              'line-width': 2,
              'line-opacity': 0.7
            }
          },
        ]
      },
      center: [-63, -38],
      zoom: 4,
      minZoom: 3,
      maxZoom: 12
    })

    map.on('load', () => {
      loading.value = false
      applyCategories(categories.value)
      applyProvince(selectedProvince.value)
      addLabels()
    })

    async function addLabels() {
      try {
        const res = await fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
        const mundo = await res.json()
        const argentina = mundo.features.find(f => f.id === 'ARG')
        if (!argentina) return

        const enArgentina = ['any', ['within', argentina]]
        const texto = ['coalesce', ['get', 'name:es'], ['get', 'name']]
        const halo = { 'text-halo-color': 'rgba(255,255,255,0.92)', 'text-halo-width': 1.2 }

        map.addLayer({
          id: 'place-suburb',
          type: 'symbol',
          source: 'omt-labels',
          'source-layer': 'place',
          filter: ['all', enArgentina, ['in', ['get', 'class'], ['literal', ['suburb', 'quarter', 'neighbourhood']]]],
          minzoom: 11,
          layout: { 'text-field': texto, 'text-font': ['Noto Sans Regular'], 'text-size': 11 },
          paint: { ...halo, 'text-color': '#888' }
        })

        map.addLayer({
          id: 'place-town',
          type: 'symbol',
          source: 'omt-labels',
          'source-layer': 'place',
          filter: ['all', enArgentina, ['in', ['get', 'class'], ['literal', ['town', 'village']]]],
          minzoom: 7,
          layout: {
            'text-field': texto,
            'text-font': ['Noto Sans Regular'],
            'text-size': ['interpolate', ['linear'], ['zoom'], 7, 10, 12, 13]
          },
          paint: { ...halo, 'text-color': '#555' }
        })

        map.addLayer({
          id: 'place-city',
          type: 'symbol',
          source: 'omt-labels',
          'source-layer': 'place',
          filter: ['all', enArgentina, ['==', ['get', 'class'], 'city']],
          minzoom: 2,
          layout: {
            'text-field': texto,
            'text-font': ['Noto Sans Regular'],
            'symbol-sort-key': ['get', 'rank'],
            'text-size': [
              'interpolate', ['linear'], ['zoom'],
              2, ['step', ['get', 'rank'], 11, 6, 8],
              8, ['step', ['get', 'rank'], 17, 6, 12]
            ]
          },
          paint: { ...halo, 'text-color': '#333' }
        })

        map.addLayer({
          id: 'place-state',
          type: 'symbol',
          source: 'omt-labels',
          'source-layer': 'place',
          filter: ['all', enArgentina, ['==', ['get', 'class'], 'state']],
          minzoom: 3,
          layout: {
            'text-field': texto,
            'text-font': ['Noto Sans Regular'],
            'text-size': ['interpolate', ['linear'], ['zoom'], 3, 9, 7, 12],
            'text-transform': 'uppercase',
            'text-letter-spacing': 0.05
          },
          paint: { ...halo, 'text-color': '#555' }
        })

        map.addLayer({
          id: 'place-country',
          type: 'symbol',
          source: 'omt-labels',
          'source-layer': 'place',
          filter: ['all', enArgentina, ['==', ['get', 'class'], 'country'], ['!=', ['get', 'iso_a2'], 'FK']],
          minzoom: 0,
          layout: {
            'text-field': texto,
            'text-font': ['Noto Sans Bold'],
            'text-size': ['interpolate', ['linear'], ['zoom'], 1, 12, 5, 16],
            'text-transform': 'uppercase',
            'text-letter-spacing': 0.06
          },
          paint: { ...halo, 'text-color': '#222' }
        })
      } catch (e) {
        console.error('[Labels]', e)
      }
    }

    map.on('click', 'nido-fill', (e) => {
      searchMarker?.remove()
      searchMarker = null
      if (!e.features?.length) return
      const p = e.features[0].properties
      if (!p) return

      popup?.remove()

      const fid = e.features[0].id
      let catColor = ''
      if (fid != null) {
        const state = map.getFeatureState({ source: 'nido', sourceLayer: 'nido', id: fid })
        const cat = state.cat
        if (cat >= 0 && cat < 5) catColor = COLORS[cat]
      }

      const vars = [
        ['Cobertura salud', 'cobertura_salud', true],
        ['Asistencia educ. 0-5', 'asiste_educ_0_5', true],
        ['Clima educ. alto/muy alto', 'clima_educ_alto_muy_alto', true],
        ['Tasa pob. activa empleada', 'tasa_pob_activa_empleada', true],
        ['Tasa empleados sector sec/ter', 'tasa_empleados_sectores_sec_ter', true],
        ['Tasa sin privaciones', 'tasa_sin_privaciones', true],
        ['Cercanía a salud', 'cercania_a_salud', false],
        ['Cercanía a jardín maternal', 'cercania_a_j_maternal', false],
        ['Cercanía a jardín infantes', 'cercania_a_j_infantes', false],
        ['Cercanía a espacios verdes', 'cercania_a_EV', false],
      ]

      let rows = ''
      for (const [label, key, isPct] of vars) {
        const val = p[key]
        rows += `<tr><td>${label}</td><td>${val != null ? (isPct ? (val * 100).toFixed(1) + '%' : quintile(val)) : '-'}</td></tr>`
      }

      popup = new maplibregl.Popup({ closeButton: false, closeOnClick: true, maxWidth: '320px' })
        .setLngLat(e.lngLat)
        .setHTML(
          `<div class="popup-content${catColor ? ' popup-bordered' : ''}"${catColor ? ` style="border-left:3px solid ${catColor}"` : ''}>
            <div class="popup-header">
              <div class="popup-title">${p.NOMPROV || ''}</div>
              <div class="popup-depto">${p.NOMDEPTO || ''}</div>
            </div>
            <table>${rows}</table>
          </div>`
        )
        .addTo(map)
    })

    map.on('mouseenter', 'nido-fill', (e) => {
      map.getCanvas().style.cursor = 'pointer'
      const f = e.features[0]
      if (f && f.id != null) {
        if (hoveredId !== null && hoveredId !== f.id) {
          map.setFeatureState({ source: 'nido', sourceLayer: 'nido', id: hoveredId }, { hover: false })
        }
        hoveredId = f.id
        map.setFeatureState({ source: 'nido', sourceLayer: 'nido', id: hoveredId }, { hover: true })
      }
    })

    map.on('mouseleave', 'nido-fill', () => {
      map.getCanvas().style.cursor = ''
      if (hoveredId !== null) {
        map.setFeatureState({ source: 'nido', sourceLayer: 'nido', id: hoveredId }, { hover: false })
        hoveredId = null
      }
    })

    map.on('click', () => {
      searchMarker?.remove()
      searchMarker = null
    })

    map.on('error', (e) => {
      console.error('[Map]', e.error?.message || e)
    })

    return () => {
      searchMarker?.remove()
      popup?.remove()
      map?.remove()
      maplibregl.removeProtocol('pmtiles')
    }
  })

  async function buscarDireccion(query) {
    searchResults = []
    if (!query.trim()) return
    const url = 'https://nominatim.openstreetmap.org/search'
      + '?format=json'
      + '&addressdetails=1'
      + '&limit=5'
      + '&countrycodes=ar'
      + '&accept-language=es'
      + '&q=' + encodeURIComponent(query)
    try {
      const res = await fetch(url)
      searchResults = await res.json()
      searchOpen = true
    } catch { searchOpen = false }
  }

  function buscar(e) {
    e?.preventDefault()
    buscarDireccion(searchQuery)
  }

  function seleccionar(r) {
    searchMarker?.remove()
    const el = document.createElement('div')
    el.className = 'search-marker'
    searchMarker = new maplibregl.Marker({ element: el })
      .setLngLat([parseFloat(r.lon), parseFloat(r.lat)])
      .addTo(map)
    map.flyTo({ center: [parseFloat(r.lon), parseFloat(r.lat)], zoom: 12 })
    searchResults = []
    searchOpen = false
    searchQuery = r.display_name
  }

  function onInput(q) {
    clearTimeout(searchTimer)
    if (q.trim()) searchTimer = setTimeout(() => buscarDireccion(q), 400)
  }

  function applyCategories(cats) {
    if (!map || !map.isStyleLoaded() || !cats) return
    for (let i = 0; i < cats.length; i++) {
      map.setFeatureState(
        { source: 'nido', sourceLayer: 'nido', id: i },
        { cat: cats[i] }
      )
    }
  }

  function applyProvince(prov) {
    if (!map || !map.isStyleLoaded()) return
    if (prov === 'Todas') {
      map.setFilter('nido-fill', null)
      map.setFilter('prov-outline', null)
      map.flyTo({ center: [-63, -38], zoom: 4 })
    } else {
      map.setFilter('nido-fill', ['==', ['get', 'NOMPROV'], prov])
      map.setFilter('prov-outline', ['==', ['get', 'NOMPROV'], prov])
      const bounds = provinceBounds.value[prov]
      if (bounds) {
        map.fitBounds(bounds, { padding: 40, maxZoom: 10 })
      }
    }
  }

  $effect(() => {
    const cats = categories.value
    if (cats) applyCategories(cats)
  })

  $effect(() => {
    const prov = selectedProvince.value
    if (map?.isStyleLoaded()) applyProvince(prov)
  })
</script>

<div bind:this={container} class="map-container"></div>

<form class="search-box" onsubmit={buscar} role="search">
  <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
    <circle cx="10" cy="10" r="7"/>
    <path d="m21 21-4.35-4.35"/>
  </svg>
  <input
    class="search-input"
    type="search"
    placeholder="Buscar localidad, calle o dirección…"
    bind:value={searchQuery}
    oninput={(e) => onInput(e.target.value)}
    onblur={() => setTimeout(() => searchOpen = false, 200)}
    onfocus={() => { if (searchResults.length) searchOpen = true }}
  />
  {#if searchOpen && searchResults.length > 0}
    <ul class="search-results" role="listbox">
      {#each searchResults as r}
        <li role="option" aria-selected={false} onmousedown={() => seleccionar(r)}>
          <svg class="loc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
          <span>{r.display_name}</span>
        </li>
      {/each}
    </ul>
  {/if}
</form>

<style>
  .map-container { position: absolute; inset: 0; }

  :global(.popup-content) {
    font-size: 0.7rem;
    line-height: 1.35;
    color: #333;
  }
  :global(.popup-bordered) {
    padding-left: 0.5rem !important;
  }
  :global(.popup-header) {
    margin-bottom: 0.3rem;
  }
  :global(.popup-title) {
    font-weight: 600;
  }
  :global(.popup-depto) {
    font-size: 0.65rem;
    color: #888;
  }
  :global(.popup-content table) {
    width: 100%;
    border-collapse: collapse;
  }
  :global(.popup-content td) {
    padding: 0.05rem 0;
  }
  :global(.popup-content td:last-child) {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
  :global(.maplibregl-popup-content) {
    background: rgba(255,255,255,0.95) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 10px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
    padding: 0.5rem 0.625rem !important;
    max-height: 340px !important;
    overflow-y: auto !important;
  }
  :global(.maplibregl-popup-tip) {
    border-top-color: rgba(255,255,255,0.95) !important;
  }

  :global(.search-marker) {
    width: 24px;
    height: 24px;
    background: var(--accent);
    border: 3px solid #fff;
    border-radius: 50%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    cursor: pointer;
    pointer-events: none;
  }

  .search-box {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 12;
    display: flex;
    align-items: center;
    gap: 0;
    max-width: 380px;
    width: calc(100% - 1.5rem);
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s var(--ease), border-color 0.2s var(--ease);
  }
  .search-box:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow), var(--shadow);
  }

  .search-icon {
    width: 1rem;
    height: 1rem;
    color: var(--muted-light);
    flex-shrink: 0;
    margin-left: 0.75rem;
  }

  .search-input {
    flex: 1;
    padding: 0.55rem 0.625rem;
    border: none;
    border-radius: var(--radius);
    font-size: 0.8rem;
    font-family: inherit;
    font-weight: 500;
    color: var(--fg);
    background: transparent;
    outline: none;
    min-width: 0;
  }
  .search-input::placeholder {
    color: var(--muted-light);
    font-weight: 400;
  }

  .search-results {
    position: absolute;
    top: calc(100% + 0.3rem);
    left: 0;
    right: 0;
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    max-height: 260px;
    overflow-y: auto;
    z-index: 13;
  }
  .search-results li {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    line-height: 1.3;
    transition: background 0.15s var(--ease);
  }
  .search-results li:hover {
    background: var(--hover);
  }
  .search-results li:last-child {
    border-bottom: none;
  }

  .loc-icon {
    width: 0.85rem;
    height: 0.85rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
    color: var(--muted-light);
  }

  @media (max-width: 768px) {
    .search-box {
      top: 3.5rem;
      left: 0.75rem;
      max-width: none;
    }
  }
</style>
