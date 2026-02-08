<template>
  <div class="assignments-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>我的作业</h3>
        </div>
      </template>
      
      <el-table :data="assignments" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.assignment_type)">
              {{ getTypeText(row.assignment_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="points" label="分值" width="80" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="handleAnswer(row)">答题</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog
      v-model="showAnswerDialog"
      title="提交作业"
      width="600px"
    >
      <div class="assignment-detail">
        <h4>{{ selectedAssignment?.title }}</h4>
        <p>{{ selectedAssignment?.content }}</p>
        
        <div v-if="selectedAssignment?.options" class="options-list">
          <el-radio-group v-model="answer" v-if="selectedAssignment.assignment_type === 'single_choice'">
            <el-radio
              v-for="(option, index) in selectedAssignment.options"
              :key="index"
              :label="String.fromCharCode(65 + index)"
            >
              {{ option }}
            </el-radio>
          </el-radio-group>
          
          <el-checkbox-group v-model="answer" v-if="selectedAssignment.assignment_type === 'multiple_choice'">
            <el-checkbox
              v-for="(option, index) in selectedAssignment.options"
              :key="index"
              :label="String.fromCharCode(65 + index)"
            >
              {{ option }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        
        <el-form v-if="selectedAssignment?.assignment_type === 'true_false'" label-width="80px">
          <el-form-item label="答案">
            <el-radio-group v-model="answer">
              <el-radio label="T">正确</el-radio>
              <el-radio label="F">错误</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        
        <el-form v-if="selectedAssignment?.assignment_type === 'short_answer'" label-width="80px">
          <el-form-item label="答案">
            <el-input
              v-model="answer"
              type="textarea"
              :rows="4"
              placeholder="请输入您的答案"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="showAnswerDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const loading = ref(false)
const assignments = ref([])
const selectedAssignment = ref(null)
const answer = ref('')
const showAnswerDialog = ref(false)

const fetchAssignments = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/assignments/student')
    assignments.value = response.data
  } catch (error) {
    console.error('Failed to fetch assignments:', error)
  } finally {
    loading.value = false
  }
}

const getTypeText = (type) => {
  const typeMap = {
    single_choice: '单选',
    multiple_choice: '多选',
    true_false: '判断',
    short_answer: '简答'
  }
  return typeMap[type] || type
}

const getTypeTag = (type) => {
  const tagMap = {
    single_choice: '',
    multiple_choice: 'warning',
    true_false: 'success',
    short_answer: 'info'
  }
  return tagMap[type] || ''
}

const handleAnswer = (assignment) => {
  selectedAssignment.value = assignment
  answer.value = ''
  showAnswerDialog.value = true
}

const handleSubmit = async () => {
  if (!answer.value) {
    ElMessage.warning('请填写答案')
    return
  }
  
  try {
    await api.post(`/api/assignments/${selectedAssignment.value.id}/submit`, {
      assignment_id: selectedAssignment.value.id,
      student_answer: answer.value
    })
    ElMessage.success('作业提交成功')
    showAnswerDialog.value = false
    fetchAssignments()
  } catch (error) {
    console.error('Failed to submit assignment:', error)
  }
}

onMounted(() => {
  fetchAssignments()
})
</script>

<style scoped>
.assignments-container {
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

.assignment-detail h4 {
  margin: 0 0 10px 0;
}

.assignment-detail p {
  color: #666;
  margin-bottom: 20px;
}

.options-list {
  margin-bottom: 20px;
}

.options-list label {
  display: block;
  margin-bottom: 10px;
}
</style>
