import { createRouter, createWebHashHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      children: [
        { path: '', component: () => import('../views/HomeView.vue') },
        { path: 'calendar', component: () => import('../views/CalendarView.vue') },
        { path: 'timeline', component: () => import('../views/TimelineView.vue') },
        { path: 'search', component: () => import('../views/SearchView.vue') },
        { path: 'trash', component: () => import('../views/TrashView.vue') },
        { path: 'settings', component: () => import('../views/SettingsView.vue') },
        { path: 'goals', component: () => import('../views/GoalsView.vue') },
        { path: 'goals/:id', component: () => import('../views/GoalDetailView.vue') },
        { path: 'reviews/date/:date', component: () => import('../views/ReviewView.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/'
  if (auth.isAuthenticated && !auth.user) {
    try { await auth.fetchMe() } catch { return '/login' }
  }
})

export default router
