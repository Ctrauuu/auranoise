<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGoalStore } from '../stores/goal'
import { localDate } from '../utils/date'

const store = useGoalStore()
const router = useRouter()
const showForm = ref(false)
const title = ref('')
const description = ref('')
const startDate = ref(localDate())
const targetDate = ref('')

const empty = computed(() => !store.goals.length)
onMounted(() => store.fetchGoals())

async function create() {
  const goal = await store.createGoal({
    title: title.value,
    description: description.value,
    start_date: startDate.value,
    target_date: targetDate.value || null,
  })
  await router.push(`/goals/${goal.id}`)
}
</script>

<template>
  <section class="mx-auto max-w-4xl">
    <header class="mb-8 flex items-center justify-between">
      <div><p class="text-sm text-stone-500">Growth</p><h1 class="text-3xl font-light">Goals</h1></div>
      <button class="rounded bg-stone-800 px-4 py-2 text-white dark:bg-stone-200 dark:text-stone-900" @click="showForm = !showForm">Add Goal</button>
    </header>
    <form v-if="showForm" class="mb-8 grid gap-4 rounded border border-stone-200 p-5 dark:border-stone-800" @submit.prevent="create">
      <label>Title<input v-model="title" required maxlength="200" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label>
      <label>Description<textarea v-model="description" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label>
      <div class="grid gap-4 sm:grid-cols-2"><label>Start date<input v-model="startDate" required type="date" class="mt-1 block w-full rounded border bg-transparent px-3 py-2" /></label><label>Target date<input v-model="targetDate" type="date" class="mt-1 block w-full rounded border bg-transparent px-3 py-2" /></label></div>
      <button class="justify-self-start rounded border border-stone-400 px-4 py-2">Create Goal</button>
    </form>
    <div v-if="empty" class="rounded border border-dashed border-stone-300 p-10 text-center"><h2 class="text-xl">No goals yet.</h2><p class="mt-2 text-stone-500">Create a goal to start tracking something that matters to you.</p></div>
    <div v-else class="space-y-3">
      <RouterLink v-for="goal in store.goals" :key="goal.id" :to="`/goals/${goal.id}`" class="block rounded border border-stone-200 p-5 hover:border-stone-400 dark:border-stone-800">
        <div class="flex items-start justify-between gap-4"><h2 class="text-lg font-medium">{{ goal.title }}</h2><span class="text-sm capitalize text-stone-500">{{ goal.status.replace('_', ' ') }}</span></div>
        <p class="mt-2 text-sm text-stone-500">{{ goal.tasks.filter(task => task.status === 'completed').length }} / {{ goal.tasks.length }} tasks completed</p>
        <p v-if="goal.target_date && goal.target_date < localDate() && goal.status !== 'completed'" class="mt-2 text-sm text-red-700">Overdue</p>
      </RouterLink>
    </div>
  </section>
</template>

