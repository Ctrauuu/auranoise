<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useGoalStore } from '../stores/goal'
import { api } from '../api/client'
import { useRouter } from 'vue-router'
import type { GoalStatus, TaskStatus } from '../types/goal'
import { localDate } from '../utils/date'

const route = useRoute()
const router = useRouter()
const store = useGoalStore()
const taskTitle = ref('')
const statuses: GoalStatus[] = ['not_started', 'active', 'completed', 'paused', 'abandoned']
const taskStatuses: TaskStatus[] = ['todo', 'in_progress', 'completed']
const completedCount = computed(() => store.current?.tasks.filter(task => task.status === 'completed').length ?? 0)

onMounted(() => store.fetchGoal(String(route.params.id)))

async function addTask() {
  if (!taskTitle.value.trim()) return
  await store.addTask(taskTitle.value.trim())
  taskTitle.value = ''
}

async function removeGoal() {
  if (!store.current || !window.confirm(`Move “${store.current.title}” to Trash?`)) return
  await api.delete(`/goals/${store.current.id}`)
  await router.push('/goals')
}
</script>

<template>
  <section v-if="store.current" class="mx-auto max-w-4xl">
    <RouterLink to="/goals" class="text-sm text-stone-500">← Goals</RouterLink>
    <header class="mt-6 flex flex-wrap items-start justify-between gap-4">
      <div><h1 class="text-3xl font-light">{{ store.current.title }}</h1><p class="mt-3 max-w-2xl whitespace-pre-wrap text-stone-600 dark:text-stone-400">{{ store.current.description }}</p></div>
      <label class="text-sm">Status<select :value="store.current.status" class="ml-2 rounded border bg-transparent px-2 py-1" @change="store.setStatus(store.current!, ($event.target as HTMLSelectElement).value as GoalStatus)"><option v-for="status in statuses" :key="status" :value="status">{{ status.replace('_', ' ') }}</option></select></label>
    </header>
    <p v-if="store.current.target_date && store.current.target_date < localDate() && store.current.status !== 'completed'" class="mt-4 text-sm text-red-700">Overdue · target {{ store.current.target_date }}</p>

    <section class="mt-10"><h2 class="text-xl">Tasks</h2><p class="mt-1 text-sm text-stone-500">{{ completedCount }} / {{ store.current.tasks.length }} tasks completed</p>
      <form class="mt-4 flex gap-2" @submit.prevent="addTask"><label class="sr-only" for="task-title">Task title</label><input id="task-title" v-model="taskTitle" required placeholder="Add a task" class="min-w-0 flex-1 rounded border bg-transparent px-3 py-2" /><button class="rounded border px-4">Add</button></form>
      <ul class="mt-4 divide-y divide-stone-200 dark:divide-stone-800"><li v-for="task in store.current.tasks" :key="task.id" class="flex items-center gap-3 py-3"><span class="flex-1" :class="task.status === 'completed' && 'line-through text-stone-500'">{{ task.title }}</span><select :value="task.status" aria-label="Task status" class="rounded border bg-transparent px-2 py-1 text-sm" @change="store.setTaskStatus(task, ($event.target as HTMLSelectElement).value as TaskStatus)"><option v-for="status in taskStatuses" :key="status" :value="status">{{ status.replace('_', ' ') }}</option></select></li></ul>
    </section>

    <section class="mt-10"><h2 class="text-xl">Timeline</h2><ol class="mt-4 border-l border-stone-300 pl-5 dark:border-stone-700"><li v-for="event in store.events" :key="event.id" class="mb-5"><p class="capitalize">{{ event.event_type.replaceAll('_', ' ') }}</p><time class="text-sm text-stone-500">{{ new Date(event.created_at).toLocaleString() }}</time></li></ol></section>
    <button class="mt-10 text-sm text-red-700" @click="removeGoal">Delete Goal</button>
  </section>
</template>
