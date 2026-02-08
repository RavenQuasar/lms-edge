<template>
  <div class="assignments-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>作业管理</h3>
              <el-button type="primary" @click="showCreateDialog = true">
                <el-icon><Plus /></el-icon>
                创建作业
              </el-button>
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
            <el-table-column prop="points" label="分值" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '激活' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="handleViewSubmissions(row)">
                  查看提交 ({{ row.submission_count || 0 }})
                </el-button>
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-dialog
      v-model="showCreateDialog"
      title="创建作业"
      width="600px"
    >
      <el-form :model="assignmentForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="assignmentForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="assignmentForm.content"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="assignmentForm.assignment_type" style="width: 100%" @change="handleTypeChange">
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multiple_choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="简答题" value="short_answer" />
          </el-select>
        </el-form-item>
        <el-form-item label="选项" v-if="['single_choice', 'multiple_choice'].includes(assignmentForm.assignment_type)">
          <el-input
            v-model="assignmentForm.options"
            type="textarea"
            placeholder="每行一个选项"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="正确答案">
          <el-input
            v-model="assignmentForm.correct_answer"
            placeholder="单选题输入选项序号，多选题用逗号分隔，判断题输入 T/F"
          />
        </el-form-item>
        <el-form-item label="分值">
          <el-input-number v-model="assignmentForm.points" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showSubmissionsDialog"
      title="作业提交"
      width="800px"
    >
      <el-table :data="submissions" stripe>
        <el-table-column prop="user_id" label="学生ID" width="80" />
        <el-table-column prop="student_answer" label="答案" />
        <el-table-column prop="is_correct" label="正确性" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_correct ? 'success' : 'danger'">
              {{ row.is_correct ? '正确' : '错误' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="得分" width="80" />
        <el-table-column prop="submitted_at" label="提交时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="handleGrade(row)">评分</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/services/api'

const loading = ref(false)
const assignments = ref([])
const submissions = ref([])
const showCreateDialog = ref(false)
const showSubmissionsDialog = ref(false)
const selectedAssignment = ref(null)

const assignmentForm = reactive({
  title: '',
  content: '',
  assignment_type: 'single_choice',
  options: '',
  correct_answer: '',
  points: 10
})

const fetchAssignments = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/assignments/')
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

const handleTypeChange = () => {
  assignmentForm.options = ''
  assignmentForm.correct_answer = ''
}

const handleCreate = async () => {
  try {
    const formData = { ...assignmentForm }
    if (formData.options) {
      formData.options = formData.options.split('\n').filter(o => o.trim())
    }
    await api.post('/api/assignments/', formData)
    ElMessage.success('作业创建成功')
    showCreateDialog.value = false
    fetchAssignments()
  } catch (error) {
    console.error('Failed to create assignment:', error)
  }
}

const handleEdit = (assignment) => {
  ElMessage.info('编辑功能待实现')
}

const handleDelete = async (assignmentId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个作业吗？', '确认删除', {
      type: 'warning'
    })
    await api.delete(`/api/assignments/${assignmentId}`)
    ElMessage.success('作业删除成功')
    fetchAssignments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete assignment:', error)
    }
  }
}

const handleViewSubmissions = async (assignment) => {
  selectedAssignment.value = assignment
  try {
    const response = await api.get(`/api/assignments/${assignment.id}/submissions`)
    submissions.value = response.data
    showSubmissionsDialog.value = true
  } catch (error) {
    console.error('Failed to fetch submissions:', error)
  }
}

const handleGrade = (submission) => {
  ElMessage.info('评分功能待实现')
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
</style>
