<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'

const auth = useAuthStore()
const settings = useSettingsStore()
onMounted(() => settings.fetchSettings(auth.user?.id))
</script>

<template>
  <div class="min-h-screen md:grid md:grid-cols-[240px_1fr]">
    <aside class="border-b border-stone-200 p-6 md:min-h-screen md:border-b-0 md:border-r dark:border-stone-800">
      <RouterLink to="/" class="text-lg font-medium tracking-wide">Auranoise</RouterLink>
      <nav class="mt-10" aria-label="Main navigation">
        <p class="mb-2 text-xs uppercase tracking-widest text-stone-500">Daily</p>
        <RouterLink to="/" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Today</RouterLink>
        <RouterLink to="/calendar" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Calendar</RouterLink>
        <RouterLink to="/timeline" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Timeline</RouterLink>
        <p class="mb-2 mt-7 text-xs uppercase tracking-widest text-stone-500">Growth</p>
        <RouterLink to="/goals" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Goals</RouterLink>
        <p class="mb-2 mt-7 text-xs uppercase tracking-widest text-stone-500">Library</p>
        <RouterLink to="/search" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Search</RouterLink>
        <RouterLink to="/trash" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Trash</RouterLink>
        <p class="mb-2 mt-7 text-xs uppercase tracking-widest text-stone-500">System</p>
        <RouterLink to="/settings" class="block rounded px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-800">Settings</RouterLink>
      </nav>
      <button class="mt-10 text-sm text-stone-500 hover:text-stone-900" @click="auth.logout(); $router.push('/login')">Sign out</button>
    </aside>
    <main class="p-6 md:p-12"><RouterView /></main>
  </div>
</template>
