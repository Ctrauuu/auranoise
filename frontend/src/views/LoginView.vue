<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')

async function submit() {
  try {
    await auth.login(username.value, password.value)
    await router.push('/')
  } catch { /* store exposes the message */ }
}
</script>

<template>
  <main class="grid min-h-screen place-items-center p-6">
    <form class="w-full max-w-sm space-y-5" @submit.prevent="submit">
      <div>
        <p class="mb-2 text-sm uppercase tracking-[0.28em] text-stone-500">Auranoise</p>
        <h1 class="text-3xl font-light">Welcome back</h1>
      </div>
      <label class="block">Username<input v-model="username" required autocomplete="username" class="mt-2 w-full rounded border border-stone-300 bg-transparent px-3 py-2" /></label>
      <label class="block">Password<input v-model="password" required type="password" autocomplete="current-password" class="mt-2 w-full rounded border border-stone-300 bg-transparent px-3 py-2" /></label>
      <p v-if="auth.error" role="alert" class="text-sm text-red-700">{{ auth.error }}</p>
      <button :disabled="auth.loading" class="w-full rounded bg-stone-800 px-4 py-2 text-white disabled:opacity-50">{{ auth.loading ? 'Signing in…' : 'Sign in' }}</button>
    </form>
  </main>
</template>

