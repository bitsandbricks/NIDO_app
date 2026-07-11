const BINS = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
const LABELS = ['Muy bajo', 'Bajo', 'Medio', 'Alto', 'Muy alto']

self.onmessage = function (e) {
  const { dims, weights, numFeatures } = e.data

  const rawValues = new Float32Array(numFeatures)
  const categories = new Uint8Array(numFeatures)

  let min = Infinity
  let max = -Infinity

  for (let i = 0; i < numFeatures; i++) {
    const off = i * 4
    let raw = 0
    let hasNaN = false
    for (let j = 0; j < 4; j++) {
      const v = dims[off + j]
      if (isNaN(v)) { hasNaN = true; break }
      raw += v * weights[j]
    }

    if (hasNaN) {
      rawValues[i] = NaN
      categories[i] = 255
      continue
    }

    rawValues[i] = raw
    if (raw < min) min = raw
    if (raw > max) max = raw
  }

  const range = max - min

  for (let i = 0; i < numFeatures; i++) {
    if (categories[i] === 255) continue
    const normalized = range > 0 ? (rawValues[i] - min) / range : 0.5

    if (normalized <= 0.2) categories[i] = 0
    else if (normalized <= 0.4) categories[i] = 1
    else if (normalized <= 0.6) categories[i] = 2
    else if (normalized <= 0.8) categories[i] = 3
    else categories[i] = 4
  }

  self.postMessage(
    { categories: categories.buffer },
    [categories.buffer]
  )
}
