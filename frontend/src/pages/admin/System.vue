<template>
  <div class="system-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon cpu"><Cpu /></el-icon>
            <div class="stat-info">
              <h3>CPU 使用率</h3>
              <p class="stat-value">{{ systemInfo.cpu_usage }}%</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon memory"><DataAnalysis /></el-icon>
            <div class="stat-info">
              <h3>内存使用</h3>
              <p class="stat-value">{{ systemInfo.memory_usage }}%</p>
              <p class="stat-sub">{{ systemInfo.memory_total.toFixed(1) }} GB</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon disk"><Coin /></el-icon>
            <div class="stat-info">
              <h3>磁盘使用</h3>
              <p class="stat-value">{{ systemInfo.disk_usage }}%</p>
              <p class="stat-sub">{{ systemInfo.disk_total.toFixed(1) }} GB</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon temp"><Box /></el-icon>
            <div class="stat-info">
              <h3>温度</h3>
              <p class="stat-value">{{ systemInfo.temperature || 'N/A' }}°C</p>
              <p class="stat-sub">{{ systemInfo.uptime }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>运行进程</h3>
              <el-button size="small" @click="fetchSystemInfo">刷新</el-button>
            </div>
          </template>
          <el-table :data="processes" stripe>
            <el-table-column prop="pid" label="PID" width="100" />
            <el-table-column prop="name" label="进程名" width="200" />
            <el-table-column prop="cpu_percent" label="CPU %" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.cpu_percent" :stroke-width="8" />
              </template>
            </el-table-column>
            <el-table-column prop="memory_percent" label="内存 %" width="150">
              <template #default="{ row }">
                {{ row.memory_percent.toFixed(1) }}%
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
              <h3>系统日志</h3>
            </div>
          </template>
          <el-scrollbar height="300px">
            <div class="logs-content">
              <div
                v-for="(log, index) in logs"
                :key="index"
                class="log-line"
              >
                {{ log }}
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const systemInfo = ref({
  cpu_usage: 0,
  cpu_count: 0,
  memory_usage: 0,
  memory_total: 0,
  disk_usage: 0,
  disk_total: 0,
  temperature: null,
  uptime: '0h 0m'
})

const processes = ref([])
const logs = ref([])

let refreshInterval = null

const fetchSystemInfo = async () => {
  try {
    const response = await api.get('/api/system/info')
    systemInfo.value = response.data
  } catch (error) {
    console.error('Failed to fetch system info:', error)
  }
}

const fetchProcesses = async () => {
  try {
    const response = await api.get('/api/system/processes')
    processes.value = response.data.processes
  } catch (error) {
    console.error('Failed to fetch processes:', error)
  }
}

const fetchLogs = async () => {
  try {
    const response = await api.get('/api/system/logs')
    logs.value = response.data.logs
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

onMounted(() => {
  fetchSystemInfo()
  fetchProcesses()
  fetchLogs()
  
  refreshInterval = setInterval(() => {
    fetchSystemInfo()
    fetchProcesses()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.system-container {
  padding: 20px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 40px;
  opacity: 0.8;
}

.stat-icon.cpu {
  color: #409eff;
}

.stat-icon.memory {
  color: #67c23a;
}

.stat-icon.disk {
  color: #e6a23c;
}

.stat-icon.temp {
  color: #f56c6c;
}

.stat-info h3 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #666;
}

.stat-value {
  margin: 0 0 0 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-sub {
  margin: 0 0 0 0;
  font-size: 12px;
  color: #999;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.logs-content {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.log-line {
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}
</style>
