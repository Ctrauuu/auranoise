export interface TrashItem {
  type: 'review' | 'section' | 'preset' | 'goal' | 'task'
  id: string
  title: string
  deleted_at: string
  metadata: Record<string, string>
}

