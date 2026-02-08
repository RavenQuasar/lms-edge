import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { io } from 'socket.io-client'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref(null)
  const connected = ref(false)
  const onlineUsers = ref([])
  const boardData = ref([])
  const boardMessages = ref([])
  
  const onlineStudentCount = computed(() => {
    return onlineUsers.value.filter(u => u.role === 'student').length
  })
  
  function connect(token, boardId = null) {
    if (socket.value?.connected) {
      socket.value.disconnect()
    }
    
    socket.value = io('ws://localhost:8000', {
      query: { token, board_id: boardId },
      transports: ['websocket']
    })
    
    socket.value.on('connect', () => {
      connected.value = true
      console.log('WebSocket connected')
    })
    
    socket.value.on('disconnect', () => {
      connected.value = false
      console.log('WebSocket disconnected')
    })
    
    socket.value.on('online_users', (data) => {
      onlineUsers.value = data.data
    })
    
    socket.value.on('draw', (data) => {
      boardData.value.push(data.data)
    })
    
    socket.value.on('message', (data) => {
      boardMessages.value.push(data.data)
    })
    
    socket.value.on('clear', () => {
      boardData.value = []
    })
    
    socket.value.on('activity_update', (data) => {
      const index = onlineUsers.value.findIndex(u => u.user_id === data.data.user_id)
      if (index !== -1) {
        onlineUsers.value[index] = { ...onlineUsers.value[index], ...data.data }
      }
    })
    
    socket.value.on('quiz_result', (data) => {
      console.log('Quiz result:', data.data)
    })
    
    socket.value.on('signin_status', (data) => {
      console.log('Signin status:', data.data)
    })
  }
  
  function disconnect() {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      connected.value = false
      onlineUsers.value = []
      boardData.value = []
      boardMessages.value = []
    }
  }
  
  function sendDraw(data) {
    if (socket.value?.connected) {
      socket.value.emit('message', {
        type: 'board_draw',
        data
      })
    }
  }
  
  function sendMessage(boardId, message) {
    if (socket.value?.connected) {
      socket.value.emit('message', {
        type: 'board_message',
        data: {
          board_id: boardId,
          message
        }
      })
    }
  }
  
  function clearBoard(boardId) {
    if (socket.value?.connected) {
      socket.value.emit('message', {
        type: 'board_clear',
        data: {}
      })
    }
  }
  
  function sendActivityUpdate(isActive, visible) {
    if (socket.value?.connected) {
      socket.value.emit('message', {
        type: 'activity_update',
        data: {
          is_active: isActive,
          visible
        }
      })
    }
  }
  
  return {
    socket,
    connected,
    onlineUsers,
    boardData,
    boardMessages,
    onlineStudentCount,
    connect,
    disconnect,
    sendDraw,
    sendMessage,
    clearBoard,
    sendActivityUpdate
  }
})
