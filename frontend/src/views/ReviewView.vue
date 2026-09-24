<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import { useAuthStore } from '../stores/auth'
import { useReviewStore } from '../stores/review'
import { useGoalStore } from '../stores/goal'
import { useSettingsStore } from '../stores/settings'
import { api } from '../api/client'
import { clearDraft, loadDraft, saveDraft } from '../utils/draft'
import { isFutureDate, longDate } from '../utils/date'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useReviewStore()
const goalStore = useGoalStore()
const settingsStore = useSettingsStore()
const date = computed(() => String(route.params.date))
const loading = ref(true)
const error = ref('')
const recovery = ref<ReturnType<typeof loadDraft>>(null)
const newTitle = ref('')
const saveToLibrary = ref(false)
const linkedGoalIds = ref<string[]>([])
let timer: ReturnType<typeof setTimeout> | undefined

onMounted(async () => {
  if (isFutureDate(date.value)) {
    error.value = 'Reviews cannot be created for future dates.'
    loading.value = false
    return
  }
  try {
    await store.openDate(date.value)
    await store.fetchSnapshots()
    await goalStore.fetchGoals()
    linkedGoalIds.value = (await api.get<{ goal_ids: string[] }>(`/reviews/${store.current!.id}/goals`)).data.goal_ids
    if (auth.user && store.current) recovery.value = loadDraft(auth.user.id, store.current)
  } catch {
    error.value = 'Unable to open this review.'
  } finally {
    loading.value = false
  }
})

watch(() => store.current?.sections, () => {
  if (!auth.user || !store.current || loading.value) return
  saveDraft(auth.user.id, store.current)
  clearTimeout(timer)
  timer = setTimeout(saveAll, settingsStore.value.autosave_seconds * 1000)
}, { deep: true })

onUnmounted(() => clearTimeout(timer))

async function saveAll() {
  if (!store.current) return
  try {
    await Promise.all(store.current.sections.map(store.saveSection))
    if (auth.user) clearDraft(auth.user.id, store.current.review_date)
  } catch { /* local draft remains available */ }
}

function restore() {
  if (!store.current || !recovery.value) return
  const recovered = new Map(recovery.value.sections.map((section) => [section.id, section]))
  store.current.sections.forEach((section) => Object.assign(section, recovered.get(section.id)))
  recovery.value = null
}

function discard() {
  if (auth.user && store.current) clearDraft(auth.user.id, store.current.review_date)
  recovery.value = null
}

async function addSection() {
  if (!newTitle.value.trim()) return
  await store.addSection(newTitle.value.trim(), saveToLibrary.value)
  newTitle.value = ''
  saveToLibrary.value = false
}

async function complete() {
  await saveAll()
  await store.complete()
}

async function saveGoalLinks() {
  if (store.current) await api.put(`/reviews/${store.current.id}/goals`, { goal_ids: linkedGoalIds.value })
}

async function removeReview() {
  if (!store.current || !window.confirm('Move this review to Trash?')) return
  await api.delete(`/reviews/${store.current.id}`)
  await router.push('/calendar')
}
</script>

<template>
  <div class="mx-auto max-w-4xl">
    <p v-if="loading">Loading…</p>
    <p v-else-if="error" role="alert" class="text-red-700">{{ error }}</p>
    <template v-else-if="store.current">
      <header class="mb-10 flex items-end justify-between gap-4">
        <div><p class="text-sm text-stone-500">Daily Review</p><h1 class="text-3xl font-light">{{ longDate(date) }}</h1></div>
        <div class="text-right text-sm text-stone-500">
          <span class="rounded border border-stone-300 px-2 py-1 dark:border-stone-700">{{ store.current.status === 'completed' ? 'Completed' : 'Draft' }}</span>
          <p v-if="store.saveState === 'saving'">Saving…</p>
          <p v-else-if="store.saveState === 'failed'" class="text-red-700">Save failed</p>
          <p v-else-if="store.savedAt">Saved at {{ store.savedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</p>
          <button class="mt-1 underline" @click="saveAll">Save</button>
        </div>
      </header>

      <aside v-if="recovery" class="mb-8 rounded border border-amber-300 bg-amber-50 p-4 text-stone-900">
        <p>Unsynced draft found.</p>
        <div class="mt-2 flex gap-3"><button class="underline" @click="restore">Restore Draft</button><button class="underline" @click="discard">Discard</button></div>
      </aside>

      <section v-for="section in store.current.sections" :key="section.id" class="mb-10">
        <div class="mb-3 flex items-center gap-3">
          <input v-model="section.title" :aria-label="`Title for ${section.title}`" class="min-w-0 flex-1 bg-transparent text-xl font-medium" />
          <button class="text-sm text-stone-500 hover:text-red-700" :aria-label="`Delete ${section.title}`" @click="store.removeSection(section)">Delete</button>
        </div>
        <MarkdownEditor v-model="section.content_markdown" />
      </section>

      <form class="rounded border border-dashed border-stone-300 p-4 dark:border-stone-700" @submit.prevent="addSection">
        <label class="block text-sm">New section title<input v-model="newTitle" maxlength="120" class="mt-2 w-full rounded border border-stone-300 bg-transparent px-3 py-2 dark:border-stone-700" /></label>
        <label class="mt-3 flex items-center gap-2 text-sm"><input v-model="saveToLibrary" type="checkbox" /> Save to section library</label>
        <button class="mt-3 rounded bg-stone-800 px-3 py-2 text-sm text-white dark:bg-stone-200 dark:text-stone-900">Add Section</button>
      </form>
      <fieldset v-if="goalStore.goals.length" class="mt-8 rounded border border-stone-200 p-4 dark:border-stone-800">
        <legend class="px-2">Related Goals</legend>
        <label v-for="goal in goalStore.goals" :key="goal.id" class="mr-5 inline-flex items-center gap-2"><input v-model="linkedGoalIds" type="checkbox" :value="goal.id" @change="saveGoalLinks" /> {{ goal.title }}</label>
      </fieldset>

      <div class="mt-8 flex items-center justify-between border-t border-stone-200 pt-8 dark:border-stone-800">
        <p class="text-sm text-stone-500">Completing creates an immutable snapshot. You can still edit afterward.</p>
        <button class="rounded bg-stone-800 px-4 py-2 text-white dark:bg-stone-200 dark:text-stone-900" @click="complete">Complete Review</button>
      </div>
      <details v-if="store.snapshots.length" class="mt-8">
        <summary class="cursor-pointer">Snapshot history ({{ store.snapshots.length }})</summary>
        <article v-for="snapshot in store.snapshots" :key="snapshot.id" class="mt-4 rounded border border-stone-200 p-4 dark:border-stone-800">
          <p class="text-sm text-stone-500">Version {{ snapshot.version }} · {{ new Date(snapshot.created_at).toLocaleString() }}</p>
          <details v-for="section in snapshot.snapshot.sections" :key="section.id" class="mt-3">
            <summary>{{ section.title }}</summary><pre class="mt-2 whitespace-pre-wrap text-sm">{{ section.content_markdown }}</pre>
          </details>
        </article>
      </details>
      <button class="mt-10 text-sm text-red-700" @click="removeReview">Delete Review</button>
    </template>
  </div>
</template>
