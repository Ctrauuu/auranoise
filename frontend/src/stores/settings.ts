import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type { UserSettings } from '../types/settings'

export function applyTheme(theme: UserSettings['theme']) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  document.documentElement.classList.toggle('light', theme === 'light')
  document.documentElement.style.colorScheme = theme === 'system' ? 'light dark' : theme
}

export const useSettingsStore = defineStore('settings', () => {
  const value = ref<UserSettings>({
    timezone: 'UTC', theme: 'system', autosave_seconds: 3, markdown_view: 'single',
    show_active_goals: true, show_tasks_due_today: true, trash_retention_days: 30,
  })
  const loaded = ref(false)

  async function fetchSettings(userId?: string) {
    value.value = (await api.get<UserSettings>('/settings')).data
    const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const initializationKey = userId ? `auranoise:timezone-initialized:${userId}` : ''
    if (initializationKey && !localStorage.getItem(initializationKey)) {
      if (browserZone && value.value.timezone === 'UTC') {
        value.value = (await api.patch<UserSettings>('/settings', { timezone: browserZone })).data
      }
      localStorage.setItem(initializationKey, 'true')
    }
    applyTheme(value.value.theme)
    loaded.value = true
  }

  async function update(patch: Partial<UserSettings>) {
    const previous = { ...value.value }
    value.value = { ...value.value, ...patch }
    if (patch.theme) applyTheme(patch.theme)
    try {
      value.value = (await api.patch<UserSettings>('/settings', patch)).data
      applyTheme(value.value.theme)
    } catch (error) {
      value.value = previous
      applyTheme(previous.theme)
      throw error
    }
  }

  return { value, loaded, fetchSettings, update }
})

