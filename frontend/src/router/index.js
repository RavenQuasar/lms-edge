import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/pages/admin/Index.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: '',
        redirect: '/admin/users'
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/pages/admin/Users.vue')
      },
      {
        path: 'system',
        name: 'AdminSystem',
        component: () => import('@/pages/admin/System.vue')
      }
    ]
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/pages/teacher/Index.vue'),
    meta: { requiresAuth: true, roles: ['teacher', 'admin'] },
    children: [
      {
        path: '',
        redirect: '/teacher/assignments'
      },
      {
        path: 'assignments',
        name: 'TeacherAssignments',
        component: () => import('@/pages/teacher/Assignments.vue')
      },
      {
        path: 'attendance',
        name: 'TeacherAttendance',
        component: () => import('@/pages/teacher/Attendance.vue')
      },
      {
        path: 'board',
        name: 'TeacherBoard',
        component: () => import('@/pages/teacher/Board.vue')
      },
      {
        path: 'stats',
        name: 'TeacherStats',
        component: () => import('@/pages/teacher/Stats.vue')
      }
    ]
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/pages/student/Index.vue'),
    meta: { requiresAuth: true, roles: ['student'] },
    children: [
      {
        path: '',
        redirect: '/student/assignments'
      },
      {
        path: 'assignments',
        name: 'StudentAssignments',
        component: () => import('@/pages/student/Assignments.vue')
      },
      {
        path: 'board',
        name: 'StudentBoard',
        component: () => import('@/pages/student/Board.vue')
      },
      {
        path: 'profile',
        name: 'StudentProfile',
        component: () => import('@/pages/student/Profile.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  if (token && to.path === '/login') {
    next('/dashboard')
    return
  }
  
  if (to.meta.roles && userStore.user) {
    if (!to.meta.roles.includes(userStore.user.role)) {
      next('/dashboard')
      return
    }
  }
  
  next()
})

export default router
