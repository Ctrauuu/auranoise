export interface UserSettings {
  timezone: string
  theme: 'system' | 'light' | 'dark'
  autosave_seconds: number
  markdown_view: 'single' | 'split'
  show_active_goals: boolean
  show_tasks_due_today: boolean
  trash_retention_days: 7 | 30 | 90 | null
}

