import { describe, expect, it } from 'vitest'
import { AxiosError } from 'axios'
import { normalizeApiError } from './client'

describe('API error normalization', () => {
  it('normalizes network errors', () => {
    expect(normalizeApiError(new AxiosError('offline')).code).toBe('NETWORK_ERROR')
  })

  it('preserves server error schemas', () => {
    const error = new AxiosError('bad', 'ERR', undefined, undefined, {
      data: { code: 'EXAMPLE', message: 'Example', details: null }, status: 409,
      statusText: 'Conflict', headers: {}, config: { headers: {} } as never,
    })
    expect(normalizeApiError(error).code).toBe('EXAMPLE')
  })
})
