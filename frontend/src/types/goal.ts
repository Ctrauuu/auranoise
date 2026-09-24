export type GoalStatus = 'not_started' | 'active' | 'completed' | 'paused' | 'abandoned'
export type TaskStatus = 'todo' | 'in_progress' | 'completed'

export interface GoalTask {
  id: string
  title: string
  description: string
  due_date: string | null
  status: TaskStatus
}

export interface Goal {
  id: string
  title: string
  description: string
  status: GoalStatus
  start_date: string
  target_date: string | null
  created_at: string
  updated_at: string
  tasks: GoalTask[]
}

export interface GoalEvent {
  id: string
  event_type: string
  event_data: Record<string, string>
  created_at: string
}

