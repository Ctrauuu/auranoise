import { describe, expect, it } from 'vitest'
import dayjs from 'dayjs'
import { isFutureDate } from './date'

describe('date utilities', () => {
  it('rejects tomorrow but permits today', () => {
    expect(isFutureDate(dayjs().format('YYYY-MM-DD'))).toBe(false)
    expect(isFutureDate(dayjs().add(1, 'day').format('YYYY-MM-DD'))).toBe(true)
  })
})
