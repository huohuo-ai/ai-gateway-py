import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import { login as loginApi, getUserInfo } from '@/api/auth'

const TOKEN_KEY = 'ai_gateway_token'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(Cookies.get(TOKEN_KEY) || '')
  const userInfo = ref(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  // Actions
  const setToken = (newToken) => {
    token.value = newToken
    Cookies.set(TOKEN_KEY, newToken, { expires: 1 })
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    Cookies.remove(TOKEN_KEY)
  }

  const login = async (credentials) => {
    const res = await loginApi(credentials)
    setToken(res.access_token)
    // 登录接口已经返回了完整用户信息，直接复用
    if (res.user) {
      userInfo.value = res.user
    }
    return res
  }

  const fetchUserInfo = async () => {
    try {
      const res = await getUserInfo()
      userInfo.value = res
      return res
    } catch (error) {
      console.error('fetchUserInfo failed:', error)
      // 失败时返回默认值，避免阻塞流程
      return null
    }
  }

  const logout = () => {
    clearToken()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    isAdmin,
    login,
    fetchUserInfo,
    logout
  }
})
