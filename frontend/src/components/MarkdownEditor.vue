<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { renderMarkdown } from '../utils/markdown'
import { useSettingsStore } from '../stores/settings'

const model = defineModel<string>({ required: true })
const settings = useSettingsStore()
const split = ref(settings.value.markdown_view === 'split')
watch(() => settings.value.markdown_view, (view) => { split.value = view === 'split' })
const textarea = ref<HTMLTextAreaElement>()
const preview = computed(() => renderMarkdown(model.value))

function wrap(before: string, after = before) {
  const element = textarea.value
  if (!element) return
  const start = element.selectionStart
  const end = element.selectionEnd
  model.value = model.value.slice(0, start) + before + model.value.slice(start, end) + after + model.value.slice(end)
  requestAnimationFrame(() => element.focus())
}
</script>

<template>
  <div>
    <div class="mb-2 flex flex-wrap items-center gap-1" aria-label="Markdown formatting">
      <button type="button" aria-label="Heading" @click="wrap('## ', '')">H</button>
      <button type="button" aria-label="Bold" @click="wrap('**')"><strong>B</strong></button>
      <button type="button" aria-label="Italic" @click="wrap('*')"><em>I</em></button>
      <button type="button" aria-label="List" @click="wrap('- ', '')">List</button>
      <button type="button" aria-label="Quote" @click="wrap('> ', '')">Quote</button>
      <button type="button" aria-label="Inline code" @click="wrap('`')">Code</button>
      <button type="button" aria-label="Code block" @click="wrap('```\n', '\n```')">Block</button>
      <button type="button" aria-label="Link" @click="wrap('[', '](https://)')">Link</button>
      <button type="button" class="ml-auto" @click="split = !split">{{ split ? 'Edit only' : 'Split view' }}</button>
    </div>
    <div :class="split ? 'grid gap-4 md:grid-cols-2' : ''">
      <textarea ref="textarea" v-model="model" rows="9" aria-label="Section content" class="w-full resize-y rounded border border-stone-300 bg-transparent p-3 leading-7 dark:border-stone-700" />
      <!-- Content is sanitized in renderMarkdown before v-html. -->
      <article v-if="split" class="prose min-h-56 rounded border border-stone-200 p-4 dark:border-stone-800" v-html="preview" />
    </div>
  </div>
</template>

<style scoped>
button { border-radius: .25rem; padding: .25rem .5rem; color: #57534e; }
button:hover { background: #e7e5e4; }
</style>
