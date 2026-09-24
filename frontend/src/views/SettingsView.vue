<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import type { UserSettings } from '../types/settings'

interface TemplateItem { id?: string; title: string; sort_order: number }
interface Preset { id: string; title: string }
interface ImportSummary { schema_version: number; reviews: number; sections: number; goals: number; tasks: number; confirmed: boolean }

const auth = useAuthStore()
const store = useSettingsStore()
const form = reactive<UserSettings>({ ...store.value })
const templateItems = ref<TemplateItem[]>([])
const presets = ref<Preset[]>([])
const newPreset = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const message = ref('')
const importFile = ref<File>()
const importSummary = ref<ImportSummary>()

onMounted(async () => {
  if (!store.loaded) await store.fetchSettings(auth.user?.id)
  Object.assign(form, store.value)
  templateItems.value = (await api.get<{ items: TemplateItem[] }>('/review-template')).data.items
  presets.value = (await api.get<Preset[]>('/section-presets')).data
})

async function saveSettings() {
  await store.update({ ...form })
  message.value = 'Settings saved.'
}

async function saveTemplate() {
  templateItems.value = (await api.put<{ items: TemplateItem[] }>('/review-template', {
    items: templateItems.value.map((item, sort_order) => ({ title: item.title, sort_order })),
  })).data.items
  message.value = 'Default review template saved.'
}

function move(index: number, amount: number) {
  const target = index + amount
  if (target < 0 || target >= templateItems.value.length) return
  const [item] = templateItems.value.splice(index, 1)
  if (item) templateItems.value.splice(target, 0, item)
}

async function addPreset() {
  if (!newPreset.value.trim()) return
  presets.value.push((await api.post<Preset>('/section-presets', { title: newPreset.value.trim() })).data)
  newPreset.value = ''
}

async function renamePreset(preset: Preset) {
  await api.patch(`/section-presets/${preset.id}`, { title: preset.title })
}

async function removePreset(preset: Preset) {
  if (!window.confirm(`Move “${preset.title}” to Trash?`)) return
  await api.delete(`/section-presets/${preset.id}`)
  presets.value = presets.value.filter(({ id }) => id !== preset.id)
}

async function changePassword() {
  if (!window.confirm('Change your password now? You will need the new password next time you sign in.')) return
  await api.post('/auth/change-password', { current_password: currentPassword.value, new_password: newPassword.value })
  currentPassword.value = ''
  newPassword.value = ''
  message.value = 'Password changed.'
}

async function download(kind: 'json' | 'markdown' | 'zip') {
  const { data } = await api.get<Blob>(`/export/${kind}`, { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = kind === 'json' ? 'auranoise-backup.json' : `auranoise-${kind}.zip`
  link.click()
  URL.revokeObjectURL(url)
}

function selectImport(event: Event) {
  importFile.value = (event.target as HTMLInputElement).files?.[0]
  importSummary.value = undefined
}

async function importBackup(confirm = false) {
  if (!importFile.value) return
  if (confirm && !window.confirm('Import this backup? All records are validated and imported in one transaction.')) return
  const body = new FormData()
  body.append('file', importFile.value)
  importSummary.value = (await api.post<ImportSummary>('/import/json', body, { params: { confirm } })).data
  message.value = confirm ? 'Backup imported.' : 'Backup validated. Review the summary before confirming.'
}
</script>

<template>
  <section class="mx-auto max-w-4xl space-y-12">
    <header><p class="text-sm text-stone-500">System</p><h1 class="text-3xl font-light">Settings</h1><p v-if="message" role="status" class="mt-4 rounded bg-stone-100 p-3 text-sm dark:bg-stone-800">{{ message }}</p></header>

    <section><h2 class="text-xl">Account</h2><p class="mt-2 text-sm text-stone-500">Username: {{ auth.user?.username }}</p>
      <form class="mt-4 grid max-w-lg gap-3" @submit.prevent="changePassword"><label>Current password<input v-model="currentPassword" required type="password" autocomplete="current-password" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label><label>New password<input v-model="newPassword" required minlength="10" type="password" autocomplete="new-password" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label><button class="justify-self-start rounded border px-4 py-2">Change Password</button></form>
    </section>

    <form class="space-y-10" @submit.prevent="saveSettings">
      <section><h2 class="text-xl">Appearance</h2><div class="mt-4 flex gap-2"><label v-for="theme in ['system', 'light', 'dark']" :key="theme" class="cursor-pointer rounded border px-4 py-2 capitalize" :class="form.theme === theme && 'border-stone-800 bg-stone-100 dark:border-stone-200 dark:bg-stone-800'"><input v-model="form.theme" class="sr-only" type="radio" :value="theme" @change="store.update({ theme: form.theme })" />{{ theme }}</label></div></section>
      <section><h2 class="text-xl">Timezone</h2><label class="mt-4 block max-w-lg">IANA timezone<input v-model="form.timezone" required list="timezones" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label><datalist id="timezones"><option value="UTC"/><option value="Asia/Shanghai"/><option value="Asia/Tokyo"/><option value="Europe/London"/><option value="America/New_York"/><option value="America/Los_Angeles"/></datalist></section>
      <section><h2 class="text-xl">Review</h2><div class="mt-4 grid max-w-lg gap-3 sm:grid-cols-2"><label>Auto-save interval<input v-model.number="form.autosave_seconds" type="number" min="2" max="10" class="mt-1 w-full rounded border bg-transparent px-3 py-2" /></label><label>Default Markdown view<select v-model="form.markdown_view" class="mt-1 w-full rounded border bg-transparent px-3 py-2"><option value="single">Single</option><option value="split">Split</option></select></label></div></section>
      <section><h2 class="text-xl">Today</h2><label class="mt-4 flex gap-2"><input v-model="form.show_active_goals" type="checkbox" /> Show Active Goals</label><label class="mt-2 flex gap-2"><input v-model="form.show_tasks_due_today" type="checkbox" /> Show Tasks Due Today</label></section>
      <section><h2 class="text-xl">Trash</h2><label class="mt-4 block max-w-sm">Retention<select v-model="form.trash_retention_days" class="mt-1 w-full rounded border bg-transparent px-3 py-2"><option :value="7">7 days</option><option :value="30">30 days</option><option :value="90">90 days</option><option :value="null">Never</option></select></label><RouterLink to="/trash" class="mt-3 inline-block text-sm underline">Open Trash</RouterLink></section>
      <button class="rounded bg-stone-800 px-5 py-2 text-white dark:bg-stone-200 dark:text-stone-900">Save Settings</button>
    </form>

    <section><h2 class="text-xl">Default Review Template</h2><p class="mt-2 text-sm text-stone-500">Changes only affect future reviews.</p><ul class="mt-4 max-w-xl space-y-2"><li v-for="(item, index) in templateItems" :key="item.id ?? index" class="flex gap-2"><input v-model="item.title" maxlength="120" class="min-w-0 flex-1 rounded border bg-transparent px-3 py-2" /><button aria-label="Move up" @click="move(index, -1)">↑</button><button aria-label="Move down" @click="move(index, 1)">↓</button><button aria-label="Remove item" class="text-red-700" @click="templateItems.splice(index, 1)">Delete</button></li></ul><button class="mt-3 rounded border px-3 py-2" @click="templateItems.push({ title: 'New Section', sort_order: templateItems.length })">Add Item</button><button class="ml-2 rounded border px-3 py-2" @click="saveTemplate">Save Template</button></section>

    <section><h2 class="text-xl">Section Library</h2><form class="mt-4 flex max-w-xl gap-2" @submit.prevent="addPreset"><input v-model="newPreset" maxlength="120" placeholder="New section label" class="min-w-0 flex-1 rounded border bg-transparent px-3 py-2" /><button class="rounded border px-3">Add</button></form><ul class="mt-3 max-w-xl"><li v-for="preset in presets" :key="preset.id" class="flex gap-2 py-2"><input v-model="preset.title" class="min-w-0 flex-1 bg-transparent" @change="renamePreset(preset)" /><button class="text-sm text-red-700" @click="removePreset(preset)">Delete</button></li></ul></section>

    <section><h2 class="text-xl">Backup</h2><div class="mt-4 flex flex-wrap gap-2"><button class="rounded border px-3 py-2" @click="download('json')">Export JSON</button><button class="rounded border px-3 py-2" @click="download('markdown')">Export Markdown</button><button class="rounded border px-3 py-2" @click="download('zip')">Export ZIP</button></div><div class="mt-5 max-w-xl rounded border border-stone-200 p-4 dark:border-stone-800"><label>Import JSON<input accept="application/json,.json" type="file" class="mt-2 block" @change="selectImport" /></label><button :disabled="!importFile" class="mt-3 rounded border px-3 py-2 disabled:opacity-50" @click="importBackup(false)">Validate Backup</button><div v-if="importSummary" class="mt-4 text-sm"><p>Schema {{ importSummary.schema_version }} · {{ importSummary.reviews }} reviews · {{ importSummary.sections }} sections · {{ importSummary.goals }} goals · {{ importSummary.tasks }} tasks</p><button v-if="!importSummary.confirmed" class="mt-3 rounded bg-stone-800 px-3 py-2 text-white dark:bg-stone-200 dark:text-stone-900" @click="importBackup(true)">Confirm Import</button></div></div></section>

    <section><h2 class="text-xl">AI</h2><p class="mt-2 text-stone-500">AI features are not enabled yet.</p></section>
    <section><h2 class="text-xl">Data Management</h2><p class="mt-2 text-stone-500">Use Backup to keep a portable copy of your data, and Trash to restore recently deleted items.</p></section>
  </section>
</template>

