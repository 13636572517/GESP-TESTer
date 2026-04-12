import request from '../utils/request'

export const getExamTemplates = (params) => request.get('/exams/templates/', { params })
export const startExam = (data) => request.post('/exams/start/', data)
export const getExam = (recordId) => request.get(`/exams/${recordId}/`)
export const saveExamAnswer = (recordId, data) => request.post(`/exams/${recordId}/answer/`, data)
export const submitExam = (recordId, data) => request.post(`/exams/${recordId}/submit/`, data)
export const reportSwitch = (recordId) => request.post(`/exams/${recordId}/switch/`)
export const getExamResult = (recordId) => request.get(`/exams/${recordId}/result/`)
export const getExamHistory = (params) => request.get('/exams/history/', { params })
