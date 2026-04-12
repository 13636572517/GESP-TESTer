import request from '../utils/request'

export const sendSms = (data) => request.post('/auth/sms/send/', data)
export const registerUser = (data) => request.post('/auth/register/', data)
export const loginByPassword = (data) => request.post('/auth/login/', data)
export const loginBySms = (data) => request.post('/auth/login/sms/', data)
export const resetPassword = (data) => request.post('/auth/password/reset/', data)
