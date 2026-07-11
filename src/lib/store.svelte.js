function createReactive(initial) {
  let v = $state(initial)
  return {
    get value() { return v },
    set value(val) { v = val }
  }
}

export const dims = createReactive(null)
export const categories = createReactive(null)
export const selectedProvince = createReactive('Todas')
export const provinces = createReactive([])
export const provinceBounds = createReactive({})
export const loading = createReactive(true)

export const weights = $state({
  salud: 100,
  educacion: 66,
  contexto: 66,
  ambiente: 33
})

export const weightLabels = ['Nula', 'Baja', 'Media', 'Alta']
export const weightValues = [0, 33, 66, 100]
