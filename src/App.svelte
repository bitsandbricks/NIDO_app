<script>
  import { onMount } from 'svelte'
  import Map from './lib/Map.svelte'
  import Sidebar from './lib/Sidebar.svelte'
  import Legend from './lib/Legend.svelte'
  import {
    dims, categories, selectedProvince, provinces,
    provinceBounds, loading, weights
  } from './lib/store.svelte.js'

  let sidebarOpen = $state(false)
  let worker = $state(null)
  let computeTimeout

  onMount(() => {
    loadData()
  })

  async function loadData() {
    try {
      const [dimResp, provResp, boundsResp] = await Promise.all([
        fetch('/data/dims.bin'),
        fetch('/data/provinces.json'),
        fetch('/data/province_bounds.json')
      ])

      const provData = await provResp.json()
      provinces.value = provData
      provinceBounds.value = await boundsResp.json()

      const dimBuffer = await dimResp.arrayBuffer()
      dims.value = new Float32Array(dimBuffer)

      const w = new Worker(
        new URL('./lib/nido.worker.js', import.meta.url),
        { type: 'module' }
      )

      w.onmessage = (e) => {
        categories.value = new Uint8Array(e.data.categories)
      }

      worker = w
      loading.value = false
    } catch (err) {
      console.error('Error loading data:', err)
      loading.value = false
    }
  }

  function runComputation(immediate) {
    clearTimeout(computeTimeout)
    if (immediate) doCompute()
    else computeTimeout = setTimeout(doCompute, 150)
    function doCompute() {
      const d = dims.value
      const w = worker
      if (!d || !w) return
      w.postMessage({
        dims: d,
        weights: [weights.salud, weights.educacion, weights.contexto, weights.ambiente],
        numFeatures: d.length / 4
      })
    }
  }

  $effect(() => {
    if (dims.value && worker) runComputation(true)
  })

  $effect(() => {
    if (weights.salud || weights.educacion || weights.contexto || weights.ambiente) {
      runComputation()
    }
  })
</script>

<div class="app-layout">
  {#if sidebarOpen}
    <div class="backdrop" role="presentation" onclick={() => sidebarOpen = false} onkeydown={() => sidebarOpen = false}></div>
  {/if}

  {#if !sidebarOpen}
    <div class="edge-peek"></div>
  {/if}

  <div class="sidebar-panel" class:open={sidebarOpen}>
    <Sidebar />
  </div>

  <div class="map-panel">
    <Map />
    <Legend />

    {#if loading.value}
      <div class="loading-overlay">
        <div class="spinner"></div>
        <p class="loading-title">Cargando datos</p>
        <p class="loading-sub">Preparando el visualizador…</p>
      </div>
    {/if}

    <button
      class="menu-toggle"
      onclick={() => sidebarOpen = !sidebarOpen}
      aria-label="Abrir panel"
    >
      {#if sidebarOpen}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <path d="M18 6 6 18"/>
          <path d="m6 6 12 12"/>
        </svg>
      {:else}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <path d="M3 12h18"/>
          <path d="M3 6h18"/>
          <path d="M3 18h18"/>
        </svg>
        <span class="toggle-label">Panel</span>
      {/if}
    </button>
  </div>
</div>

<style>
  .app-layout {
    display: flex;
    height: 100dvh;
    width: 100vw;
    overflow: hidden;
  }

  .sidebar-panel {
    width: 340px;
    flex-shrink: 0;
    background: var(--bg);
    border-right: 1px solid var(--border);
    position: relative;
    z-index: 20;
  }

  .map-panel {
    flex: 1;
    position: relative;
    overflow: hidden;
  }

  .menu-toggle {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 15;
    display: none;
    align-items: center;
    gap: 0.375rem;
    padding: 0.55rem 0.75rem 0.55rem 0.65rem;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: var(--fg);
    font-size: 0.8rem;
    font-family: inherit;
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s var(--ease), background 0.2s var(--ease);
    line-height: 1;
  }
  .menu-toggle:hover {
    background: var(--hover);
    box-shadow: var(--shadow-sm);
  }
  .menu-toggle:active {
    transform: scale(0.97);
  }

  .toggle-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent);
  }

  .edge-peek {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--accent-darker), var(--accent));
    z-index: 15;
    pointer-events: none;
    opacity: 0.6;
  }

  .loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(6px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    z-index: 50;
  }

  .loading-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--accent-darker);
    margin: 0.5rem 0 0;
  }

  .loading-sub {
    font-size: 0.75rem;
    color: var(--muted);
    margin: 0;
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 2.5px solid var(--border-light);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 768px) {
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.35);
      z-index: 25;
      animation: fadeIn 0.25s var(--ease);
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .sidebar-panel {
      position: fixed;
      top: 0;
      left: 0;
      width: 85vw;
      max-width: 340px;
      height: 100%;
      transform: translateX(-100%);
      border-right: none;
      z-index: 30;
      transition: transform 0.3s var(--ease);
      box-shadow: 4px 0 24px rgba(0,0,0,0.1);
    }

    .sidebar-panel.open {
      transform: translateX(0);
    }

    .menu-toggle {
      display: flex;
    }

    .edge-peek {
      display: block;
    }
  }
</style>
