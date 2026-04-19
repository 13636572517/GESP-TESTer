import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('../views/auth/ResetPassword.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { auth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/home/Home.vue'),
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/knowledge/Knowledge.vue'),
      },
      {
        path: 'knowledge/:id',
        name: 'KnowledgeDetail',
        component: () => import('../views/knowledge/KnowledgeDetail.vue'),
      },
      {
        path: 'practice',
        name: 'Practice',
        component: () => import('../views/practice/Practice.vue'),
      },
      {
        path: 'practice/:id',
        name: 'PracticeSession',
        component: () => import('../views/practice/PracticeSession.vue'),
      },
      {
        path: 'practice/:id/result',
        name: 'PracticeResult',
        component: () => import('../views/practice/PracticeResult.vue'),
      },
      {
        path: 'exam',
        name: 'ExamList',
        component: () => import('../views/exam/ExamList.vue'),
      },
      {
        path: 'exam/:id/result',
        name: 'ExamResult',
        component: () => import('../views/exam/ExamResult.vue'),
      },
      {
        path: 'mistakes',
        name: 'Mistakes',
        component: () => import('../views/mistakes/Mistakes.vue'),
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('../views/stats/Stats.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/profile/Profile.vue'),
      },
      {
        path: 'ai-settings',
        name: 'UserAISettings',
        component: () => import('../views/profile/UserAISettings.vue'),
      },
      // 管理端
      {
        path: 'admin/questions',
        name: 'AdminQuestions',
        component: () => import('../views/admin/Questions.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/knowledge',
        name: 'AdminKnowledge',
        component: () => import('../views/admin/KnowledgeManage.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/exam-templates',
        name: 'AdminExamTemplates',
        component: () => import('../views/admin/ExamTemplates.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/pdf-import',
        name: 'AdminPdfImport',
        component: () => import('../views/admin/PdfImport.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/members',
        name: 'AdminMembers',
        component: () => import('../views/admin/Members.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/classes',
        name: 'AdminClasses',
        component: () => import('../views/admin/Classes.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/ai-questions',
        name: 'AdminAIQuestions',
        component: () => import('../views/admin/AIQuestions.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/ai-settings',
        name: 'AdminAISettings',
        component: () => import('../views/admin/AISettings.vue'),
        meta: { admin: true },
      },
      {
        path: 'admin/feedbacks',
        name: 'AdminFeedbacks',
        component: () => import('../views/admin/Feedbacks.vue'),
        meta: { admin: true },
      },
    ],
  },
  {
    path: '/exam/:id/session',
    name: 'ExamSession',
    component: () => import('../views/exam/ExamSession.vue'),
    meta: { auth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.auth && !userStore.isLoggedIn) {
    return next('/login')
  }

  if (to.meta.guest && userStore.isLoggedIn) {
    return next('/')
  }

  // 登录后加载用户信息
  if (userStore.isLoggedIn && !userStore.userInfo) {
    await userStore.fetchProfile()
  }

  if (to.meta.admin && !userStore.isAdmin) {
    return next('/')
  }

  next()
})

export default router
