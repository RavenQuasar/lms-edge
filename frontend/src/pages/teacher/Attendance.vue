<template>
  <div class="attendance-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>签到控制</h3>
            </div>
          </template>
          
          <div class="signin-control">
            <el-form label-width="80px">
              <el-form-item label="时长(分)">
                <el-input-number v-model="duration" :min="1" :max="30" />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  @click="startSignin"
                  :disabled="signinActive"
                  style="width: 100%"
                >
                  开始签到
                </el-button>
                <el-button
                  type="danger"
                  @click="stopSignin"
                  :disabled="!signinActive"
                  style="width: 100%; margin-top: 10px"
                >
                  结束签到
                </el-button>
              </el-form-item>
            </el-form>
            
            <el-divider />
            
            <div class="signin-status">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="状态">
                  <el-tag :type="signinActive ? 'success' : 'info'">
                    {{ signinActive ? '进行中' : '未开始' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="签到人数">
                  {{ signedCount }} / {{ totalStudents }}
                </el-descriptions-item>
                <el-descriptions-item label="过期时间">
                  {{ expiresAt || '-' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>学生状态</h3>
              <el-tag type="success" size="large">
                在线: {{ onlineCount }}
              </el-tag>
            </div>
          </template>
          
          <el-table :data="onlineUsers" stripe>
            <el-table-column prop="username" label="姓名" width="120" />
            <el-table-column label="在线状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.visible ? 'success' : 'info'">
                  {{ row.visible ? '活跃' : '隐藏' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="签到状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="hasSignedIn(row.user_id) ? 'success' : 'warning'"
                >
                  {{ hasSignedIn(row.user_id) ? '已签' : '未签' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="最近活跃" width="180">
              <template #default="{ row }">
                {{ formatTime(row.last_seen) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>考勤记录</h3>
              <el-button size="small" @click="fetchRecords">刷新</el-button>
            </div>
          </template>
          
          <el-table :data="attendanceRecords" stripe>
            <el-table-column prop="username" label="姓名" width="120" />
            <el-table-column prop="login_time" label="签到时间" width="180" />
            <el-table-column prop="logout_time" label="登出时间" width="180" />
            <el-table-column label="时长(分钟)" width="100">
              <template #default="{ row }">
                {{ Math.floor(row.session_duration / 60) }}
              </template>
            </el-table-column>
            <el-table-column label="活跃度" width="100">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'
import { useWebSocketStore } from '@/stores/websocket'
import { useUserStore } from '@/stores/user'

const wsStore = useWebSocketStore()
const userStore = useUserStore()

const duration = ref(5)
const signinActive = ref(false)
const signinId = ref(null)
const expiresAt = ref('')
const signedInUsers = ref([])
const attendanceRecords = ref([])

const onlineUsers = computed(() => {
  return wsStore.onlineUsers.filter(u => u.role === 'student')
})

const onlineCount = computed(() => onlineUsers.value.length)

const signedCount = computed(() => signedInUsers.value.length)

const totalStudents = computed(() => onlineUsers.value.length)

const startSignin = async () => {
  try {
    const response = await api.post('/api/attendance/signin', {
      duration_minutes: duration.value
    })
    signinId.value = response.data.signin_id
    expiresAt.value = new Date(response.data.expires_at).toLocaleString()
    signinActive.value = true
    signedInUsers.value = []
    ElMessage.success('签到已开始')
  } catch (error) {
    console.error('Failed to start signin:', error)
  }
}

const stopSignin = async () => {
  signinActive.value = false
  signinId.value = null
  expiresAt.value = ''
  ElMessage.success('签到已结束')
}

const fetchRecords = async () => {
  try {
    const response = await api.get('/api/attendance/records')
    attendanceRecords.value = response.data
  } catch (error) {
    console.error('Failed to fetch records:', error)
  }
}

const hasSignedIn = (userId) => {
  return signedInUsers.value.some(u => u.user_id === userId)
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

onMounted(() => {
  wsStore.connect(localStorage.getItem('token'))
  fetchRecords()
})

onUnmounted(() => {
  wsStore.disconnect()
})
</script>

<style scoped>
.attendance-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.signin-control {
  padding: 10px;
}

.signin-status {
  margin-top: 20px;
}
</style>
