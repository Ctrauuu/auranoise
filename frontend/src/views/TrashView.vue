<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import type { TrashItem } from '../types/data'

const items = ref<TrashItem[]>([])
const message = ref('')

async function load() {
  items.value = (await api.get<{ items: TrashItem[] }>('/trash', { params: { page_size: 100 } })).data.items
}

async function restore(item: TrashItem) {
  await api.post(`/trash/${item.type}/${item.id}/restore`)
  message.value = `${item.title} restored.`
  await load()
}

async function remove(item: TrashItem) {
  if (!window.confirm(`Permanently delete “${item.title}”? This cannot be undone.`)) return
  await api.delete(`/trash/${item.type}/${item.id}`)
  message.value = `${item.title} permanently deleted.`
  await load()
}

onMounted(load)
</script>

<template>
  <section class="mx-auto max-w-4xl">
    <p class="text-sm text-stone-500">Library</p><h1 class="text-3xl font-light">Trash</h1>
    <p class="mt-3 text-sm text-stone-500">Deleted items are removed automatically according to your retention setting.</p>
    <p v-if="message" role="status" class="mt-5 rounded bg-stone-100 p-3 text-sm text-stone-800 dark:bg-stone-800 dark:text-stone-100">{{ message }}</p>
    <div v-if="!items.length" class="mt-10 rounded border border-dashed border-stone-300 p-10 text-center text-stone-500">Trash is empty.</div>
    <ul v-else class="mt-8 divide-y divide-stone-200 dark:divide-stone-800"><li v-for="item in items" :key="item.id" class="flex flex-wrap items-center gap-3 py-4"><div class="min-w-0 flex-1"><p>{{ item.title }}</p><p class="text-xs capitalize text-stone-500">{{ item.type }} · Deleted {{ new Date(item.deleted_at).toLocaleString() }}</p></div><button class="rounded border px-3 py-1 text-sm" @click="restore(item)">Restore</button><button class="rounded border border-red-300 px-3 py-1 text-sm text-red-700" @click="remove(item)">Delete Permanently</button></li></ul>
  </section>
</template>

