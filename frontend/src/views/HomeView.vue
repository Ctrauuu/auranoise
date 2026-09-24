<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import { useGoalStore } from '../stores/goal'
import { useSettingsStore } from '../stores/settings'
import type { StatsSummary } from '../types/discovery'
import type { Review } from '../types/review'
import { dateInTimezone, longDate } from '../utils/date'

const settings = useSettingsStore()
const goals = useGoalStore()
const review = ref<Review | null>(null)
const stats = ref<StatsSummary>()
const loading = ref(true)
const error = ref('')
const today = computed(() => review.value?.review_date ?? dateInTimezone(settings.value.timezone))
const tasksDue = computed(() => goals.goals.flatMap(goal => goal.tasks).filter(task => task.due_date === today.value && task.status !== 'completed').length)

onMounted(async () => {
  try {
    const [reviewResponse, statsResponse] = await Promise.all([
      api.get<Review | null>('/reviews/today'), api.get<StatsSummary>('/stats/summary'), goals.fetchGoals(),
    ])
    review.value = reviewResponse.data
    stats.value = statsResponse.data
  } catch { error.value = 'Unable to load today.' }
  finally { loading.value = false }
})
</script>

<template>
  <section class="mx-auto max-w-3xl py-10">
    <p v-if="loading">Loading…</p><p v-else-if="error" role="alert" class="text-red-700">{{ error }}</p>
    <template v-else>
      <p class="text-sm text-stone-500">{{ longDate(today) }}</p>
      <h1 class="mt-3 text-4xl font-light tracking-tight">How was your day?</h1>
      <p v-if="review?.status !== 'completed'" class="mt-5 text-sm text-amber-700">You haven't completed today's review yet.</p>
      <div class="mt-10 grid gap-3 sm:grid-cols-3">
        <div class="rounded border border-stone-200 p-4 dark:border-stone-800"><p class="text-sm text-stone-500">Today's Review</p><p class="mt-1 capitalize">{{ review?.status ?? 'Not Started' }}</p></div>
        <div v-if="settings.value.show_active_goals" class="rounded border border-stone-200 p-4 dark:border-stone-800"><p class="text-sm text-stone-500">Active Goals</p><p class="mt-1 text-2xl font-light">{{ stats?.active_goals ?? 0 }}</p></div>
        <div v-if="settings.value.show_tasks_due_today" class="rounded border border-stone-200 p-4 dark:border-stone-800"><p class="text-sm text-stone-500">Tasks Due Today</p><p class="mt-1 text-2xl font-light">{{ tasksDue }}</p></div>
      </div>
      <RouterLink :to="`/reviews/date/${today}`" class="mt-8 inline-block rounded bg-stone-800 px-5 py-3 text-white dark:bg-stone-200 dark:text-stone-900">{{ review ? "Continue Today's Review" : "Start Today's Review" }}</RouterLink>
      <div v-if="stats" class="mt-12 grid grid-cols-2 gap-4 border-t border-stone-200 pt-8 text-sm dark:border-stone-800 sm:grid-cols-3"><p><span class="block text-2xl font-light">{{ stats.reviews_completed_this_month }}</span>Reviews this month</p><p><span class="block text-2xl font-light">{{ stats.current_review_streak }}</span>Current streak</p><p><span class="block text-2xl font-light">{{ stats.longest_review_streak }}</span>Longest streak</p></div>
    </template>
  </section>
</template>
