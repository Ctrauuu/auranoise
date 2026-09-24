import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'
import type { ApiError, User } from '../types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auranoise_token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref('')
  const isAuthenticated = computed(() => Boolean(token.value))

  async function login(username: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.post<{ access_token: string }>('/auth/login', { username, password })
      token.value = data.access_token
      localStorage.setItem('auranoise_token', data.access_token)
      await fetchMe()
    } catch (reason) {
      error.value = (reason as ApiError).message
      throw reason
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    const { data } = await api.get<User>('/auth/me')
    user.value = data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('auranoise_token')
  }

  return { token, user, loading, error, isAuthenticated, login, fetchMe, logout }
})

