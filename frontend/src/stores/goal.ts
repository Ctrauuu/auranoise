import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type { Goal, GoalEvent, GoalStatus, GoalTask, TaskStatus } from '../types/goal'

export const useGoalStore = defineStore('goal', () => {
  const goals = ref<Goal[]>([])
  const current = ref<Goal | null>(null)
  const events = ref<GoalEvent[]>([])

  async function fetchGoals(status?: GoalStatus) {
    goals.value = (await api.get<{ items: Goal[] }>('/goals', { params: { status, page_size: 100 } })).data.items
  }

  async function fetchGoal(id: string) {
    current.value = (await api.get<Goal>(`/goals/${id}`)).data
    events.value = (await api.get<GoalEvent[]>(`/goals/${id}/events`)).data
  }

  async function createGoal(payload: Pick<Goal, 'title' | 'description' | 'start_date' | 'target_date'>) {
    const { data } = await api.post<Goal>('/goals', payload)
    goals.value.unshift(data)
    return data
  }

  async function setStatus(goal: Goal, status: GoalStatus) {
    const previous = goal.status
    goal.status = status
    try {
      Object.assign(goal, (await api.patch<Goal>(`/goals/${goal.id}`, { status })).data)
      if (current.value?.id === goal.id) await fetchGoal(goal.id)
    } catch (error) {
      goal.status = previous
      throw error
    }
  }

  async function addTask(title: string) {
    if (!current.value) return
    const { data } = await api.post<GoalTask>(`/goals/${current.value.id}/tasks`, { title })
    current.value.tasks.push(data)
    await fetchGoal(current.value.id)
  }

  async function setTaskStatus(task: GoalTask, status: TaskStatus) {
    const previous = task.status
    task.status = status
    try {
      Object.assign(task, (await api.patch<GoalTask>(`/goal-tasks/${task.id}`, { status })).data)
      if (current.value) events.value = (await api.get<GoalEvent[]>(`/goals/${current.value.id}/events`)).data
    } catch (error) {
      task.status = previous
      throw error
    }
  }

  return { goals, current, events, fetchGoals, fetchGoal, createGoal, setStatus, addTask, setTaskStatus }
})

