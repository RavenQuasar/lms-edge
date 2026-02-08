<template>
  <div class="dashboard-container">
    <el-container>
      <el-aside width="200px">
        <div class="logo">LMS-Edge</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#001529"
          text-color="#fff"
          active-text-color="#1890ff"
        >
          <el-menu-item
            v-for="menu in menus"
            :key="menu.path"
            :index="menu.path"
          >
            <el-icon><component :is="menu.icon" /></el-icon>
            <span>{{ menu.title }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>{{ currentPageTitle }}</h2>
            <div class="user-info">
              <el-dropdown @command="handleCommand">
                <span class="user-dropdown">
                  <el-avatar :size="32" :src="user?.avatar">
                    {{ user?.username?.charAt(0)?.toUpperCase() }}
                  </el-avatar>
                  <span>{{ user?.full_name || user?.username }}</span>
                  <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                    <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useWebSocketStore } from '@/stores/websocket'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const wsStore = useWebSocketStore()

const user = computed(() => userStore.user)
const currentPageTitle = computed(() => {
  const routeMap = {
    '/admin/users': '用户管理',
    '/admin/system': '系统监控',
    '/teacher/assignments': '作业管理',
    '/teacher/attendance': '考勤管理',
    '/teacher/board': '共享白板',
    '/teacher/stats': '统计分析',
    '/student/assignments': '我的作业',
    '/student/board': '课堂白板',
    '/student/profile': '个人资料'
  }
  return routeMap[route.path] || '首页'
})

const activeMenu = computed(() => route.path)

const menus = computed(() => {
  const role = user.value?.role
  if (role === 'admin') {
    return [
      { path: '/admin/users', title: '用户管理', icon: 'User' },
      { path: '/admin/system', title: '系统监控', icon: 'Monitor' }
    ]
  } else if (role === 'teacher') {
    return [
      { path: '/teacher/assignments', title: '作业管理', icon: 'Document' },
      { path: '/teacher/attendance', title: '考勤管理', icon: 'Calendar' },
      { path: '/teacher/board', title: '共享白板', icon: 'Edit' },
      { path: '/teacher/stats', title: '统计分析', icon: 'DataAnalysis' }
    ]
  } else {
    return [
      { path: '/student/assignments', title: '我的作业', icon: 'Document' },
      { path: '/student/board', title: '课堂白板', icon: 'Edit' },
      { path: '/student/profile', title: '个人资料', icon: 'User' }
    ]
  }
})

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    wsStore.disconnect()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/student/profile')
  }
}

let visibilityHandler = null

onMounted(async () => {
  if (!user.value) {
    await userStore.getCurrentUser()
  }
  
  if (user.value?.role) {
    wsStore.connect(localStorage.getItem('token'))
  }
  
  visibilityHandler = () => {
    wsStore.sendActivityUpdate(true, !document.hidden)
  }
  document.addEventListener('visibilitychange', visibilityHandler)
})

onUnmounted(() => {
  if (visibilityHandler) {
    document.removeEventListener('visibilitychange', visibilityHandler)
  }
  wsStore.disconnect()
})
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-aside {
  background-color: #001529;
  overflow-x: hidden;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.el-header {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-dropdown:hover {
  background: #f5f5f5;
}

.el-main {
  background: #f5f5f5;
  padding: 20px;
}
</style>
