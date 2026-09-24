<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import type { Review } from '../types/review'
import { isFutureDate } from '../utils/date'

const month = ref(dayjs().startOf('month'))
const reviews = ref<Review[]>([])
const loading = ref(false)

const cells = computed(() => {
  const first = month.value.startOf('month').startOf('week')
  return Array.from({ length: 42 }, (_, index) => first.add(index, 'day'))
})
const byDate = computed(() => new Map(reviews.value.map((review) => [review.review_date, review])))

async function load() {
  loading.value = true
  const { data } = await api.get<{ items: Review[] }>('/reviews', {
    params: {
      date_from: month.value.startOf('month').format('YYYY-MM-DD'),
      date_to: month.value.endOf('month').format('YYYY-MM-DD'),
      page_size: 100,
    },
  })
  reviews.value = data.items
  loading.value = false
}

async function move(amount: number) {
  month.value = month.value.add(amount, 'month')
  await load()
}

onMounted(load)
</script>

<template>
  <section class="mx-auto max-w-5xl">
    <header class="mb-8 flex items-center justify-between">
      <button aria-label="Previous month" @click="move(-1)">←</button>
      <h1 class="text-3xl font-light">{{ month.format('MMMM YYYY') }}</h1>
      <button aria-label="Next month" @click="move(1)">→</button>
    </header>
    <div class="grid grid-cols-7 text-center text-xs uppercase tracking-wider text-stone-500">
      <span v-for="day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']" :key="day" class="py-2">{{ day }}</span>
    </div>
    <div class="grid grid-cols-7 border-l border-t border-stone-200 dark:border-stone-800" :aria-busy="loading">
      <component
        :is="isFutureDate(cell.format('YYYY-MM-DD')) ? 'div' : 'RouterLink'"
        v-for="cell in cells"
        :key="cell.format('YYYY-MM-DD')"
        :to="`/reviews/date/${cell.format('YYYY-MM-DD')}`"
        class="min-h-24 border-b border-r border-stone-200 p-2 dark:border-stone-800"
        :class="[cell.month() !== month.month() && 'opacity-35', isFutureDate(cell.format('YYYY-MM-DD')) && 'cursor-not-allowed opacity-35']"
      >
        <span>{{ cell.date() }}</span>
        <p v-if="byDate.get(cell.format('YYYY-MM-DD'))" class="mt-4 text-xs capitalize" :class="byDate.get(cell.format('YYYY-MM-DD'))?.status === 'completed' ? 'text-emerald-700' : 'text-amber-700'">
          {{ byDate.get(cell.format('YYYY-MM-DD'))?.status }}
        </p>
        <p v-else-if="!isFutureDate(cell.format('YYYY-MM-DD'))" class="mt-4 text-xs text-stone-400">No Review</p>
      </component>
    </div>
  </section>
</template>

