import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type { Review, ReviewSection, ReviewSnapshot } from '../types/review'

export const useReviewStore = defineStore('review', () => {
  const current = ref<Review | null>(null)
  const saveState = ref<'idle' | 'saving' | 'saved' | 'failed'>('idle')
  const savedAt = ref<Date | null>(null)
  const snapshots = ref<ReviewSnapshot[]>([])

  async function openDate(date: string) {
    const { data } = await api.get<{ items: Review[] }>('/reviews', {
      params: { date_from: date, date_to: date, page_size: 1 },
    })
    if (data.items[0]) current.value = data.items[0]
    else current.value = (await api.post<Review>('/reviews', { review_date: date })).data
  }

  async function saveSection(section: ReviewSection) {
    saveState.value = 'saving'
    try {
      await api.patch(`/review-sections/${section.id}`, {
        title: section.title,
        content_markdown: section.content_markdown,
      })
      saveState.value = 'saved'
      savedAt.value = new Date()
    } catch (error) {
      saveState.value = 'failed'
      throw error
    }
  }

  async function addSection(title: string, saveToLibrary = false) {
    if (!current.value) return
    const { data } = await api.post<ReviewSection>(`/reviews/${current.value.id}/sections`, {
      title,
      save_to_library: saveToLibrary,
    })
    current.value.sections.push(data)
  }

  async function removeSection(section: ReviewSection) {
    await api.delete(`/review-sections/${section.id}`)
    if (current.value) current.value.sections = current.value.sections.filter(({ id }) => id !== section.id)
  }

  async function complete() {
    if (!current.value) return
    current.value = (await api.post<Review>(`/reviews/${current.value.id}/complete`)).data
    await fetchSnapshots()
  }

  async function fetchSnapshots() {
    if (!current.value) return
    snapshots.value = (await api.get<ReviewSnapshot[]>(`/reviews/${current.value.id}/snapshots`)).data
  }

  return { current, snapshots, saveState, savedAt, openDate, saveSection, addSection, removeSection, complete, fetchSnapshots }
})
