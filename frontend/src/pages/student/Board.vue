<template>
  <div class="board-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>课堂白板</h3>
          <div class="board-controls">
            <el-color-picker v-model="currentColor" size="small" />
            <el-input-number
              v-model="brushSize"
              :min="1"
              :max="20"
              size="small"
              style="width: 80px"
            />
          </div>
        </div>
      </template>
      
      <div class="board-wrapper">
        <div ref="boardCanvas" class="board-canvas"></div>
      </div>
      
      <el-divider />
      
      <div class="board-messages">
        <div class="messages-header">
          <h4>互动留言</h4>
        </div>
        <el-scrollbar height="200px">
          <div class="messages-list">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message-item"
            >
              <el-tag size="small">{{ msg.username }}</el-tag>
              <span>{{ msg.message }}</span>
            </div>
          </div>
        </el-scrollbar>
        <div class="message-input">
          <el-input
            v-model="newMessage"
            placeholder="发送留言..."
            @keyup.enter="sendMessage"
          >
            <template #append>
              <el-button @click="sendMessage">发送</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { computed } from 'vue'
import { useWebSocketStore } from '@/stores/websocket'
import { ElMessage } from 'element-plus'
import { fabric } from 'fabric'

const wsStore = useWebSocketStore()

const boardCanvas = ref(null)
let canvas = null

const currentColor = ref('#000000')
const brushSize = ref(3)
const newMessage = ref('')

const messages = computed(() => wsStore.boardMessages)

const boardId = 'classroom-1'

const initCanvas = () => {
  if (!boardCanvas.value) return
  
  canvas = new fabric.Canvas(boardCanvas.value, {
    isDrawingMode: true,
    width: boardCanvas.value.offsetWidth,
    height: 500
  })
  
  canvas.freeDrawingBrush.width = brushSize.value
  canvas.freeDrawingBrush.color = currentColor.value
  
  canvas.on('path:created', (e) => {
    const path = e.path
    wsStore.sendDraw({
      board_id: boardId,
      action: 'draw',
      points: path.path,
      color: path.stroke,
      size: path.strokeWidth
    })
  })
}

const sendMessage = () => {
  if (!newMessage.value.trim()) return
  
  wsStore.sendMessage(boardId, newMessage.value)
  newMessage.value = ''
}

watch(currentColor, (color) => {
  if (canvas) {
    canvas.freeDrawingBrush.color = color
  }
})

watch(brushSize, (size) => {
  if (canvas) {
    canvas.freeDrawingBrush.width = size
  }
})

watch(() => wsStore.boardData, (drawData) => {
  if (canvas && drawData.length > 0) {
    const lastDraw = drawData[drawData.length - 1]
    if (lastDraw.action === 'clear') {
      canvas.clear()
    } else if (lastDraw.action === 'draw' && lastDraw.points) {
      const path = new fabric.Path(lastDraw.points.join(' '))
      path.stroke = lastDraw.color
      path.strokeWidth = lastDraw.size
      path.fill = null
      canvas.add(path)
    }
  }
}, { deep: true })

onMounted(() => {
  wsStore.connect(localStorage.getItem('token'), boardId)
  
  setTimeout(() => {
    initCanvas()
  }, 100)
  
  window.addEventListener('resize', () => {
    if (canvas && boardCanvas.value) {
      canvas.setWidth(boardCanvas.value.offsetWidth)
      canvas.renderAll()
    }
  })
})

onUnmounted(() => {
  if (canvas) {
    canvas.dispose()
  }
  wsStore.disconnect()
})
</script>

<style scoped>
.board-container {
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

.board-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.board-wrapper {
  position: relative;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.board-canvas {
  width: 100%;
  height: 500px;
}

.board-messages {
  margin-top: 20px;
}

.messages-header h4 {
  margin: 0 0 10px 0;
}

.messages-list {
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.message-item:last-child {
  border-bottom: none;
}

.message-input {
  margin-top: 10px;
}
</style>
