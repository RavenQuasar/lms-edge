import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }
  
  function setUser(userData) {
    user.value = userData
  }
  
  async function login(username, password) {
    try {
      const response = await api.post('/api/auth/login', {
        username,
        password
      })
      setToken(response.data.access_token)
      setUser(response.data.user)
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  function logout() {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }
  
  async function getCurrentUser() {
    if (!token.value) return null
    try {
      const response = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      setUser(response.data)
      return response.data
    } catch (error) {
      logout()
      return null
    }
  }
  
  return {
    user,
    token,
    setToken,
    setUser,
    login,
    logout,
    getCurrentUser
  }
})
