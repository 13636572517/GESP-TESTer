import request from '../utils/request'

export const sendSms = (data) => request.post('/auth/sms/send/', data)
export const registerUser = (data) => request.post('/auth/register/', data)
export const loginByPassword = (data) => request.post('/auth/login/', data)
export const loginBySms = (data) => request.post('/auth/login/sms/', data)
export const loginByUsername = (data) => request.post('/auth/login/username/', data)
export const resetPassword = (data) => request.post('/auth/password/reset/', data)

// 普通用户 AI 设置
export const getUserAIConfig = () => request.get('/user/ai-config/')
export const saveUserAIConfig = (data) => request.put('/user/ai-config/', data)
export const testUserAIModel = (model) => request.post('/user/ai-config/test/', { model })
export const getUserAIUsage = (days = 30) => request.get('/user/ai-usage/', { params: { days } })
