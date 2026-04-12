import request from '../utils/request'

export const startPractice = (data) => request.post('/practice/start/', data)
export const submitAnswer = (sessionId, data) => request.post(`/practice/${sessionId}/submit/`, data)
export const finishPractice = (sessionId) => request.post(`/practice/${sessionId}/finish/`)
export const getPracticeHistory = (params) => request.get('/practice/history/', { params })

// 错题本
export const getMistakes = (params) => request.get('/mistakes/', { params })
export const getMistakeStats = () => request.get('/mistakes/stats/')
export const generateReview = (data) => request.post('/mistakes/review/', data)
export const markMastered = (id) => request.put(`/mistakes/${id}/mastered/`)
