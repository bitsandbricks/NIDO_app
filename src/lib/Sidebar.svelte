<script>
  import { weights, weightLabels, weightValues, selectedProvince, provinces, loading } from './store.svelte.js'

  const dimensions = [
    { key: 'salud', label: 'Salud' },
    { key: 'educacion', label: 'Educación temprana' },
    { key: 'contexto', label: 'Contexto socioeconómico' },
    { key: 'ambiente', label: 'Ambiente saludable' }
  ]

  function setWeight(key, value) {
    weights[key] = value
  }
</script>

<aside class="sidebar">
  <div class="header">
    <h1 class="title">ÍNDICE NIDO</h1>
    <div class="title-underline"></div>
  </div>

  <div class="desc-card">
    <p class="desc-text">
      Resume cuatro dimensiones que definen el acceso a oportunidades para la primera infancia. Muestra con información precisa en dónde están las brechas de acceso a las oportunidades para la primera infancia, y señala las zonas donde una intervención puede hacer una gran diferencia.
    </p>
    <p class="desc-hint">
      Usá el panel para definir la importancia de cada aspecto. El índice se recalcula automáticamente para todas las provincias.
    </p>
  </div>

  <div class="section">
    <span class="section-label">Provincia</span>
    <div class="select-wrap">
        <select
          id="prov-select"
          bind:value={selectedProvince.value}
          disabled={loading.value}
        >
          <option value="Todas">Todas las provincias</option>
          {#each provinces.value as prov}
            <option value={prov}>{prov}</option>
          {/each}
        </select>
      </div>
  </div>

  <div class="section">
    <span class="section-label">Priorización</span>
    <div class="weights-grid">
      {#each dimensions as dim}
        <div class="weight-row">
          <span class="weight-label">{dim.label}</span>
          <div class="pills" role="radiogroup" aria-label={dim.label}>
            {#each weightLabels as label, i}
              <button
                class="pill"
                class:active={weightValues[i] === weights[dim.key]}
                onclick={() => setWeight(dim.key, weightValues[i])}
                aria-pressed={weightValues[i] === weights[dim.key]}
              >
                {label}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>

  <div class="footer">
    <img class="fractal-logo" src="/fractal.svg" alt="FRACTAL" />
    <p>NIDO es un proyecto de <a href="https://fractalargentina.org/herramienta/nido/" target="_blank" rel="noopener">FRACTAL / laboratorio de bienes públicos digitales</a></p>
  </div>
</aside>

<style>
  .sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.125rem;
    padding: 1.5rem 1.5rem 1.25rem;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    height: 100%;
  }

  .header {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .title {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    color: var(--accent-darker);
  }

  .title-underline {
    width: 2rem;
    height: 3px;
    border-radius: 2px;
    background: var(--accent);
  }

  .desc-card {
    background: var(--hover);
    border-radius: var(--radius);
    padding: 0.75rem 0.875rem;
    border-left: 3px solid var(--accent);
  }

  .desc-text {
    font-size: 0.72rem;
    color: var(--fg);
    margin: 0 0 0.5rem;
    line-height: 1.55;
  }

  .desc-hint {
    font-size: 0.68rem;
    color: var(--muted);
    margin: 0;
    line-height: 1.45;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .section-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-darker);
  }

  .select-wrap {
    position: relative;
  }

  .select-wrap select {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--bg);
    color: var(--fg);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    transition: border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
  }

  .select-wrap select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
    outline: none;
  }

  .select-wrap::after {
    content: '';
    position: absolute;
    right: 0.75rem;
    top: 50%;
    margin-top: -2px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid var(--muted);
    pointer-events: none;
  }

  .weights-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .weight-row {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .weight-label {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--fg);
  }

  .pills {
    display: flex;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
  }

  .pill {
    flex: 1;
    padding: 0.55rem 0;
    font-size: 0.78rem;
    font-weight: 600;
    border: none;
    background: var(--bg);
    color: var(--muted);
    cursor: pointer;
    transition: all 0.2s var(--ease);
    border-right: 1px solid var(--border);
  }

  .pill:last-child {
    border-right: none;
  }

  .pill.active {
    background: var(--accent-dark);
    color: #fff;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.15);
  }

  .pill:hover:not(.active) {
    background: var(--hover);
    color: var(--fg);
  }

  .pill:active {
    transform: scale(0.96);
  }

  .footer {
    margin-top: auto;
    padding-top: 0.875rem;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .fractal-logo {
    height: 20px;
    width: auto;
    margin-top: 0.15rem;
    flex-shrink: 0;
  }

  .footer p {
    font-size: 0.62rem;
    color: var(--muted-light);
    line-height: 1.4;
    margin: 0;
  }

  .footer a {
    color: var(--muted);
    font-weight: 500;
  }

  .footer a:hover {
    color: var(--accent);
  }
</style>
