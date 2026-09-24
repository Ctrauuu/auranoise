export interface SearchResult {
  type: 'review' | 'section' | 'preset' | 'goal' | 'task'
  id: string
  title: string
  snippet: string
  date: string | null
  metadata: Record<string, string>
}

export interface TimelineEntry {
  type: string
  id: string
  title: string
  occurred_at: string
  metadata: Record<string, string | number>
}

export interface StatsSummary {
  reviews_completed_this_month: number
  current_review_streak: number
  longest_review_streak: number
  active_goals: number
  completed_goals: number
  goal_tasks_completed: number
  goal_tasks_total: number
}

