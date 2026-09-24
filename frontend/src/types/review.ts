export interface ReviewSection {
  id: string
  preset_id: string | null
  title: string
  content_markdown: string
  sort_order: number
}

export interface Review {
  id: string
  review_date: string
  status: 'draft' | 'completed'
  created_at: string
  updated_at: string
  sections: ReviewSection[]
}

export interface LocalDraft {
  savedAt: string
  sections: Pick<ReviewSection, 'id' | 'title' | 'content_markdown'>[]
}

export interface ReviewSnapshot {
  id: string
  version: number
  snapshot: {
    review_date: string
    sections: Pick<ReviewSection, 'id' | 'preset_id' | 'title' | 'content_markdown' | 'sort_order'>[]
    linked_goals: unknown[]
  }
  created_at: string
}
