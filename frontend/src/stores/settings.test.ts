import { describe, expect, it } from 'vitest'
import { applyTheme } from './settings'

describe('theme settings', () => {
  it('applies an explicit dark theme', () => {
    applyTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    applyTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
