import { describe, expect, it } from 'vitest'
import { clearDraft, loadDraft, saveDraft } from './draft'
import type { Review } from '../types/review'

const review: Review = {
  id: 'review', review_date: '2026-09-24', status: 'draft',
  created_at: '2026-09-24T00:00:00Z', updated_at: '2026-09-24T00:00:00Z',
  sections: [{ id: 'section', preset_id: null, title: 'Reflection', content_markdown: 'Hello', sort_order: 0 }],
}

describe('draft recovery', () => {
  it('stores, restores and clears a newer local draft', () => {
    saveDraft('user', review)
    expect(loadDraft('user', review)?.sections[0]?.content_markdown).toBe('Hello')
    clearDraft('user', review.review_date)
    expect(loadDraft('user', review)).toBeNull()
  })
})
