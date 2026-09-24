<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '../api/client'
import type { SearchResult } from '../types/discovery'

const keyword = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const resultType = ref('')
const sectionLabel = ref('')
const results = ref<SearchResult[]>([])
const searched = ref(false)
const loading = ref(false)

const grouped = computed(() => {
  const groups = new Map<string, SearchResult[]>()
  for (const item of results.value) groups.set(item.type, [...(groups.get(item.type) ?? []), item])
  return groups
})

function href(item: SearchResult): string | undefined {
  if (item.type === 'review') return `/reviews/date/${item.date}`
  if (item.type === 'section') return `/reviews/date/${item.date}`
  if (item.type === 'goal') return `/goals/${item.id}`
  if (item.type === 'task') return `/goals/${item.metadata.goal_id}`
}

async function search() {
  loading.value = true
  try {
    const { data } = await api.get<{ items: SearchResult[] }>('/search', {
      params: {
        keyword: keyword.value,
        date_from: dateFrom.value || undefined,
        date_to: dateTo.value || undefined,
        result_type: resultType.value || undefined,
        section_label: sectionLabel.value || undefined,
        page_size: 100,
      },
    })
    results.value = data.items
    searched.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-4xl">
    <p class="text-sm text-stone-500">Library</p><h1 class="text-3xl font-light">Search</h1>
    <form class="mt-8 grid gap-3 sm:grid-cols-2" @submit.prevent="search">
      <label class="sm:col-span-2">Keyword<input v-model="keyword" maxlength="200" class="mt-1 w-full rounded border bg-transparent px-3 py-2" placeholder="Search reflections, goals, and tasks" /></label>
      <label>From<input v-model="dateFrom" type="date" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label>
      <label>To<input v-model="dateTo" type="date" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label>
      <label>Result type<select v-model="resultType" class="mt-1 w-full rounded border bg-transparent px-3 py-2"><option value="">All</option><option value="review">Reviews</option><option value="section">Review Sections</option><option value="preset">Section Labels</option><option value="goal">Goals</option><option value="task">Goal Tasks</option></select></label>
      <label>Section label<input v-model="sectionLabel" maxlength="120" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label>
      <button class="justify-self-start rounded bg-stone-800 px-5 py-2 text-white dark:bg-stone-200 dark:text-stone-900">{{ loading ? 'Searching…' : 'Search' }}</button>
    </form>
    <p v-if="searched && !results.length" class="mt-10 text-stone-500">No results found.</p>
    <div v-for="[type, items] in grouped" :key="type" class="mt-10"><h2 class="mb-3 text-sm uppercase tracking-wider text-stone-500">{{ type }}s</h2>
      <component :is="href(item) ? 'RouterLink' : 'article'" v-for="item in items" :key="item.id" :to="href(item)" class="mb-2 block rounded border border-stone-200 p-4 hover:border-stone-400 dark:border-stone-800"><h3>{{ item.title }}</h3><p class="mt-1 line-clamp-2 text-sm text-stone-500">{{ item.snippet }}</p><time v-if="item.date" class="mt-2 block text-xs text-stone-400">{{ item.date }}</time></component>
    </div>
  </section>
</template>
