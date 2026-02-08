<template>
  <div class="profile-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>个人资料</h3>
          </template>
          
          <div class="user-profile">
            <el-avatar :size="100" :src="user?.avatar">
              {{ user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div class="user-info">
              <h2>{{ user?.full_name || user?.username }}</h2>
              <el-tag :type="getRoleTag(user?.role)">
                {{ getRoleText(user?.role) }}
              </el-tag>
            </div>
            
            <el-divider />
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="用户名">
                {{ user?.username }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(user?.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="user?.is_active ? 'success' : 'info'">
                  {{ user?.is_active ? '激活' : '禁用' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>学习统计</h3>
              <el-button size="small" @click="fetchStats">刷新</el-button>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-icon sessions"><el-icon><Timer /></el-icon></div>
                <div class="stat-info">
                  <p class="stat-value">{{ stats.total_sessions }}</p>
                  <p class="stat-label">学习次数</p>
                </div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-icon duration"><el-icon><Clock /></el-icon></div>
                <div class="stat-info">
                  <p class="stat-value">{{ formatDuration(stats.total_duration) }}</p>
                  <p class="stat-label">学习时长</p>
                </div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-icon assignments"><el-icon><Document /></el-icon></div>
                <div class="stat-info">
                  <p class="stat-value">{{ stats.total_assignments }}</p>
                  <p class="stat-label">作业数量</p>
                </div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-icon correct"><el-icon><TrendCharts /></el-icon></div>
                <div class="stat-info">
                  <p class="stat-value">{{ stats.correct_rate.toFixed(1) }}%</p>
                  <p class="stat-label">正确率</p>
                </div>
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <h4>正确率趋势</h4>
          <div ref="trendChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <h3>学习记录</h3>
          </template>
          
          <el-table :data="attendanceRecords" stripe>
            <el-table-column label="序号" type="index" width="80" />
            <el-table-column prop="login_time" label="登录时间" width="180" />
            <el-table-column prop="logout_time" label="登出时间" width="180" />
            <el-table-column label="时长(分钟)" width="100">
              <template #default="{ row }">
                {{ Math.floor(row.session_duration / 60) }}
              </template>
            </el-table-column>
            <el-table-column label="活跃度" width="150">
              <template #default="{ row }">
                <el-progress :percentage="row.activity_score" />
              </template>
            </el-table-column>
            <el-table-column prop="is_late" label="迟到" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_late ? 'danger' : 'success'" size="small">
                  {{ row.is_late ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/services/api'
import * as echarts from 'echarts'

const userStore = useUserStore()

const user = computed(() => userStore.user)
const stats = ref({
  total_sessions: 0,
  total_duration: 0,
  avg_activity_score: 0,
  total_assignments: 0,
  correct_rate: 0,
  late_count: 0
})

const attendanceRecords = ref([])
const trendChart = ref(null)
let trendChartInstance = null

const fetchStats = async () => {
  try {
    const response = await api.get('/api/stats/my-stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchRecords = async () => {
  try {
    const response = await api.get('/api/attendance/my-records')
    attendanceRecords.value = response.data
  } catch (error) {
    console.error('Failed to fetch records:', error)
  }
}

const fetchTrend = async () => {
  if (!user.value) return
  
  try {
    const response = await api.get(`/api/stats/trend/${user.value.id}`)
    updateTrendChart(response.data)
  } catch (error) {
    console.error('Failed to fetch trend:', error)
  }
}

const updateTrendChart = (data) => {
  if (!trendChart.value) return
  
  const dates = data.map(d => d.date.split('T')[0])
  const rates = data.map(d => d.correct_rate)
  
  if (trendChartInstance) {
    trendChartInstance.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value',
        max: 100
      },
      series: [{
        name: '正确率',
        type: 'line',
        data: rates,
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          color: 'rgba(103, 194, 58, 0.1)'
        }
      }]
    })
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}

const getRoleText = (role) => {
  const roleMap = {
    admin: '管理员',
    teacher: '老师',
    student: '学生'
  }
  return roleMap[role] || role
}

const getRoleTag = (role) => {
  const tagMap = {
    admin: 'danger',
    teacher: 'warning',
    student: 'success'
  }
  return tagMap[role] || ''
}

onMounted(async () => {
  await userStore.getCurrentUser()
  fetchStats()
  fetchRecords()
  fetchTrend()
  
  setTimeout(() => {
    if (trendChart.value) {
      trendChartInstance = echarts.init(trendChart.value)
    }
  }, 100)
  
  window.addEventListener('resize', () => {
    if (trendChartInstance) {
      trendChartInstance.resize()
    }
  })
})

onUnmounted(() => {
  if (trendChartInstance) {
    trendChartInstance.dispose()
  }
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
}

.user-profile {
  text-align: center;
}

.user-profile .el-avatar {
  margin-bottom: 20px;
}

.user-info {
  margin-bottom: 20px;
}

.user-info h2 {
  margin: 0 0 10px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.sessions {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-icon.duration {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.assignments {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.correct {
  background: #f9f0ff;
  color: #722ed1;
}

.stat-info p {
  margin: 0;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #666;
}
</style>
