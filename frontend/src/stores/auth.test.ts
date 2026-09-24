import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from './auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('logs out locally', () => {
    localStorage.setItem('auranoise_token', 'token')
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    store.logout()
    expect(store.isAuthenticated).toBe(false)
  })
})
