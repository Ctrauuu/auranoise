import type { LocalDraft, Review } from '../types/review'

export const draftKey = (userId: string, date: string) => `auranoise:draft:${userId}:${date}`

export function saveDraft(userId: string, review: Review): void {
  const draft: LocalDraft = {
    savedAt: new Date().toISOString(),
    sections: review.sections.map(({ id, title, content_markdown }) => ({ id, title, content_markdown })),
  }
  localStorage.setItem(draftKey(userId, review.review_date), JSON.stringify(draft))
}

export function loadDraft(userId: string, review: Review): LocalDraft | null {
  try {
    const value = localStorage.getItem(draftKey(userId, review.review_date))
    if (!value) return null
    const draft = JSON.parse(value) as LocalDraft
    return new Date(draft.savedAt) > new Date(review.updated_at) ? draft : null
  } catch {
    return null
  }
}

export function clearDraft(userId: string, date: string): void {
  localStorage.removeItem(draftKey(userId, date))
}

