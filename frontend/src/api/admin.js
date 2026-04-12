import request from '../utils/request'

// 题目管理
export const getQuestions = (params) => request.get('/admin/questions/', { params })
export const createQuestion = (data) => request.post('/admin/questions/', data)
export const updateQuestion = (id, data) => request.put(`/admin/questions/${id}/`, data)
export const deleteQuestion = (id) => request.delete(`/admin/questions/${id}/`)

// 批量操作
export const batchCreateQuestions = (data) => request.post('/admin/questions/batch/', data)
export const batchDeleteQuestions = (ids) => request.post('/admin/questions/batch-delete/', { ids })

// CSV导入
export const importCsvQuestions = (formData) => request.post('/admin/questions/import-csv/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

// 导出题目（返回原始 response，包含 blob 和 headers）
import axios from 'axios'
import { useUserStore } from '../stores/user'

function authBlobGet(url, params = {}) {
  const userStore = useUserStore()
  return axios.get(url, {
    baseURL: '/api',
    params,
    responseType: 'blob',
    headers: userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {},
  })
}

export const exportQuestions = (params) => authBlobGet('/admin/questions/export/', params)
export const downloadCsvTemplate = () => authBlobGet('/admin/questions/csv-template/')

// 试卷模板管理
export const getExamTemplates = (params) => request.get('/admin/exam-templates/', { params })
export const createExamTemplate = (data) => request.post('/admin/exam-templates/', data)
export const updateExamTemplate = (id, data) => request.put(`/admin/exam-templates/${id}/`, data)

// 知识点内容编辑
export const updateKnowledgeContent = (id, data) => request.post(`/admin/knowledge/${id}/content/`, data)

// 知识点CSV导入/导出
export const importKnowledgeCsv = (formData) => request.post('/admin/knowledge/import-csv/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const downloadKnowledgeCsvTemplate = () => authBlobGet('/admin/knowledge/csv-template/')
export const exportKnowledgeCsv = (params) => authBlobGet('/admin/knowledge/export/', params)
