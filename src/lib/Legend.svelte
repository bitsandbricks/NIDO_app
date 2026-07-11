<script>
  const labels = ['Muy alto', 'Alto', 'Medio', 'Bajo', 'Muy bajo']
  const colors = ['#3288bd', '#99d594', '#fee08b', '#fc8d59', '#d53e4f']
</script>

<div class="legend">
  <span class="legend-title">NIDO</span>
  <div class="legend-items">
    {#each labels as label, i}
      <div class="legend-item">
        <span class="swatch" style="background: {colors[i]}"></span>
        <span class="label">{label}</span>
      </div>
    {/each}
  </div>
</div>

<style>
  .legend {
    position: absolute;
    bottom: 3rem;
    right: 1rem;
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: var(--radius);
    padding: 0.75rem 0.875rem;
    box-shadow: var(--shadow);
    z-index: 10;
    min-width: 100px;
    user-select: none;
  }

  .legend-title {
    font-size: 0.8rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-darker);
    display: block;
    margin-bottom: 0.35rem;
  }

  .legend-items {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    flex-shrink: 0;
  }

  .label {
    font-size: 0.78rem;
    color: var(--fg);
    font-weight: 500;
    line-height: 1;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .legend {
      bottom: 2.5rem;
      right: 0.75rem;
      padding: 0.5rem 0.625rem;
    }
    .swatch {
      width: 12px;
      height: 12px;
    }
    .label {
      font-size: 0.72rem;
    }
  }
</style>
