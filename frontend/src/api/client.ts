import axios, { AxiosError } from 'axios'
import type { ApiError } from '../types/auth'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
})

export function normalizeApiError(error: AxiosError<ApiError>): ApiError {
  if (error.response?.data?.code && error.response.data.message) return error.response.data
  const messages: Record<number, string> = {
    401: 'Your session has expired.', 403: 'You do not have permission to do that.',
    404: 'The requested item was not found.', 409: 'This conflicts with existing data.',
    422: 'Please check the information you entered.', 500: 'The server could not complete the request.',
  }
  return {
    code: error.response ? `HTTP_${error.response.status}` : 'NETWORK_ERROR',
    message: error.response ? (messages[error.response.status] ?? 'The request failed.') : 'Unable to reach the server.',
    details: null,
  }
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auranoise_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(undefined, (error: AxiosError<ApiError>) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('auranoise_token')
    if (location.hash !== '#/login') location.hash = '#/login'
  }
  return Promise.reject(normalizeApiError(error))
})
