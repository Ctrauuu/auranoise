<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import type { TimelineEntry } from '../types/discovery'

const filter = ref('')
const entries = ref<TimelineEntry[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    entries.value = (await api.get<{ items: TimelineEntry[] }>('/timeline', {
      params: { type: filter.value || undefined, page_size: 100 },
    })).data.items
  } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <section class="mx-auto max-w-3xl">
    <header class="flex items-end justify-between"><div><p class="text-sm text-stone-500">Daily</p><h1 class="text-3xl font-light">Timeline</h1></div><div role="group" aria-label="Timeline filters" class="flex gap-1"><button v-for="item in [{label:'All',value:''},{label:'Reviews',value:'reviews'},{label:'Goals',value:'goals'},{label:'Tasks',value:'tasks'}]" :key="item.value" class="rounded px-3 py-1 text-sm" :class="filter === item.value ? 'bg-stone-800 text-white dark:bg-stone-200 dark:text-stone-900' : 'text-stone-500'" @click="filter = item.value; load()">{{ item.label }}</button></div></header>
    <p v-if="loading" class="mt-8">Loading…</p>
    <p v-else-if="!entries.length" class="mt-8 text-stone-500">Your timeline is quiet for now.</p>
    <ol v-else class="mt-10 border-l border-stone-300 pl-6 dark:border-stone-700"><li v-for="entry in entries" :key="entry.id" class="relative mb-7 before:absolute before:-left-[1.8rem] before:top-2 before:h-2 before:w-2 before:rounded-full before:bg-stone-500"><p>{{ entry.title }}</p><time class="text-sm text-stone-500">{{ new Date(entry.occurred_at).toLocaleString() }}</time></li></ol>
  </section>
</template>

