import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截器
request.interceptors.request.use(config => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  async error => {
    const { response } = error
    if (response) {
      if (response.status === 401) {
        const userStore = useUserStore()
        // 尝试刷新token
        if (userStore.refreshToken && !error.config._retry) {
          error.config._retry = true
          try {
            const res = await axios.post('/api/auth/token/refresh/', {
              refresh: userStore.refreshToken,
            })
            userStore.setTokens(res.data.access, userStore.refreshToken)
            error.config.headers.Authorization = `Bearer ${res.data.access}`
            return request(error.config)
          } catch {
            userStore.logout()
            router.push('/login')
          }
        } else {
          userStore.logout()
          router.push('/login')
        }
      } else if (response.status === 403) {
        ElMessage.error('没有权限')
      } else if (response.data?.detail) {
        ElMessage.error(response.data.detail)
      } else {
        ElMessage.error('请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
