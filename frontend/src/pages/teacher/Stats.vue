<template>
  <div class="stats-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon students"><el-icon><User /></el-icon></div>
            <div class="stat-info">
              <h3>学生总数</h3>
              <p class="stat-value">{{ classStats.total_students }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon active"><el-icon><Connection /></el-icon></div>
            <div class="stat-info">
              <h3>在线学生</h3>
              <p class="stat-value">{{ classStats.active_students }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon assignments"><el-icon><Document /></el-icon></div>
            <div class="stat-info">
              <h3>作业总数</h3>
              <p class="stat-value">{{ classStats.total_assignments }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon score"><el-icon><TrendCharts /></el-icon></div>
            <div class="stat-info">
              <h3>平均得分</h3>
              <p class="stat-value">{{ classStats.avg_score.toFixed(1) }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>作业统计</h3>
            </div>
          </template>
          <div ref="assignmentChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>正确率分布</h3>
            </div>
          </template>
          <div ref="correctnessChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>作业详细统计</h3>
              <div>
                <el-button size="small" @click="exportAttendance">导出考勤</el-button>
                <el-button size="small" @click="exportAssignments">导出作业</el-button>
              </div>
            </div>
          </template>
          
          <el-table :data="assignmentStats" stripe>
            <el-table-column prop="assignment_id" label="ID" width="80" />
            <el-table-column prop="title" label="标题" width="200" />
            <el-table-column prop="total_submissions" label="提交数" width="100" />
            <el-table-column prop="correct_count" label="正确数" width="100" />
            <el-table-column label="正确率" width="150">
              <template #default="{ row }">
                <el-progress :percentage="row.correct_rate" />
              </template>
            </el-table-column>
            <el-table-column prop="avg_score" label="平均分" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'
import * as echarts from 'echarts'

const assignmentChart = ref(null)
const correctnessChart = ref(null)

let assignmentChartInstance = null
let correctnessChartInstance = null

const classStats = ref({
  total_students: 0,
  active_students: 0,
  total_assignments: 0,
  avg_score: 0,
  total_sessions: 0
})

const assignmentStats = ref([])

const fetchClassStats = async () => {
  try {
    const response = await api.get('/api/stats/class')
    classStats.value = response.data
  } catch (error) {
    console.error('Failed to fetch class stats:', error)
  }
}

const fetchAssignmentStats = async () => {
  try {
    const response = await api.get('/api/stats/assignments/all')
    assignmentStats.value = response.data
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch assignment stats:', error)
  }
}

const updateCharts = () => {
  if (!assignmentChart.value || !correctnessChart.value) return
  
  const titles = assignmentStats.value.map(s => s.title)
  const submissionCounts = assignmentStats.value.map(s => s.total_submissions)
  const correctRates = assignmentStats.value.map(s => s.correct_rate)
  
  if (assignmentChartInstance) {
    assignmentChartInstance.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: titles
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        name: '提交数',
        type: 'bar',
        data: submissionCounts,
        itemStyle: {
          color: '#409eff'
        }
      }]
    })
  }
  
  if (correctnessChartInstance) {
    correctnessChartInstance.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: titles
      },
      yAxis: {
        type: 'value',
        max: 100
      },
      series: [{
        name: '正确率',
        type: 'line',
        data: correctRates,
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

const exportAttendance = async () => {
  try {
    const response = await api.get('/api/stats/export/attendance', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'attendance.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    ElMessage.success('考勤数据导出成功')
  } catch (error) {
    console.error('Failed to export attendance:', error)
  }
}

const exportAssignments = async () => {
  try {
    const response = await api.get('/api/stats/export/assignments', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'assignments.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    ElMessage.success('作业数据导出成功')
  } catch (error) {
    console.error('Failed to export assignments:', error)
  }
}

onMounted(() => {
  fetchClassStats()
  fetchAssignmentStats()
  
  setTimeout(() => {
    if (assignmentChart.value) {
      assignmentChartInstance = echarts.init(assignmentChart.value)
    }
    if (correctnessChart.value) {
      correctnessChartInstance = echarts.init(correctnessChart.value)
    }
    updateCharts()
  }, 100)
  
  window.addEventListener('resize', () => {
    if (assignmentChartInstance) {
      assignmentChartInstance.resize()
    }
    if (correctnessChartInstance) {
      correctnessChartInstance.resize()
    }
  })
})

onUnmounted(() => {
  if (assignmentChartInstance) {
    assignmentChartInstance.dispose()
  }
  if (correctnessChartInstance) {
    correctnessChartInstance.dispose()
  }
})
</script>

<style scoped>
.stats-container {
  padding: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
}

.stat-icon.students {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-icon.active {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.assignments {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.score {
  background: #f9f0ff;
  color: #722ed1;
}

.stat-info h3 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: #666;
}

.stat-value {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}
</style>
