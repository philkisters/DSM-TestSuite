const STORAGE_KEY = 'dsm-settings'

export default defineNuxtPlugin(() => {
  const settings = useSettingsStore()

  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') as Record<string, unknown>
    // Only accept known keys with a matching type, so stale or corrupt data can't break the defaults.
    // Nullable settings default to null and hold numbers when set.
    const matches = (value: unknown, defaultValue: unknown) =>
      defaultValue === null ? value === null || typeof value === 'number' : typeof value === typeof defaultValue
    const valid = Object.fromEntries(
      Object.entries(settings.$state).filter(([key, defaultValue]) => matches(saved[key], defaultValue))
        .map(([key]) => [key, saved[key]])
    )
    settings.$patch(valid)
  } catch {
    localStorage.removeItem(STORAGE_KEY)
  }

  settings.$subscribe((_mutation, state) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  })
})
