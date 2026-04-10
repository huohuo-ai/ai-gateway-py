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
    return res
  }

  const fetchUserInfo = async () => {
    const res = await getUserInfo()
    userInfo.value = res
    return res
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
