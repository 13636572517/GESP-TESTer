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
export const patchExamTemplate = (id, data) => request.patch(`/admin/exam-templates/${id}/`, data)
export const deleteExamTemplate = (id) => request.delete(`/admin/exam-templates/${id}/`)

// PDF 题目提取 —— 用独立 axios 实例，避免全局 15s 超时 + 拦截器重复弹窗
export function pdfExtract(formData) {
  const userStore = useUserStore()
  return axios.post('/api/admin/questions/pdf-extract/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
    },
    timeout: 300000, // 5 分钟，大 PDF 多页识别需要足够长
  }).then(res => res.data)
}
export const pdfImportConfirm = (questions) => request.post('/admin/questions/pdf-import/', { questions })

// 会员管理
export const getAdminUsers = (params) => request.get('/admin/users/', { params })
export const createAdminUser = (data) => request.post('/admin/users/', data)
export const updateAdminUser = (id, data) => request.put(`/admin/users/${id}/`, data)
export const deleteAdminUser = (id) => request.delete(`/admin/users/${id}/`)

// 班级管理
export const getClassrooms = (params) => request.get('/admin/classes/', { params })
export const createClassroom = (data) => request.post('/admin/classes/', data)
export const updateClassroom = (id, data) => request.put(`/admin/classes/${id}/`, data)
export const deleteClassroom = (id) => request.delete(`/admin/classes/${id}/`)
export const getClassroomMembers = (id) => request.get(`/admin/classes/${id}/members/`)
export const addClassroomMember = (id, data) => request.post(`/admin/classes/${id}/members/`, data)
export const removeClassroomMember = (classId, memberId) => request.delete(`/admin/classes/${classId}/members/${memberId}/`)

// AI 功能
// 单题标注：60s 超时，避免多题批量时 15s 全局超时导致网络错误
export const aiSuggestTagOne      = (questionId)  => request.post('/admin/questions/ai-suggest-tags/', { question_ids: [questionId] }, { timeout: 60000 })
export const aiConfirmTags        = (items)       => request.post('/admin/questions/ai-confirm-tags/', items)
export const aiGenerateQuestions  = (data)        => request.post('/admin/questions/ai-generate/', data, { timeout: 120000 })

// AI 配置与统计
export const getAIConfig      = ()      => request.get('/admin/ai-config/')
export const saveAIConfig     = (data)  => request.put('/admin/ai-config/', data)
export const testAIModel      = (model) => request.post('/admin/ai-config/test/', { model }, { timeout: 60000 })
export const getAIUsageStats  = (days)  => request.get('/admin/ai-usage/', { params: { days } })

// 知识点内容编辑
export const updateKnowledgeContent = (id, data) => request.post(`/admin/knowledge/${id}/content/`, data)

// 知识点CSV导入/导出
export const importKnowledgeCsv = (formData) => request.post('/admin/knowledge/import-csv/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const downloadKnowledgeCsvTemplate = () => authBlobGet('/admin/knowledge/csv-template/')
export const exportKnowledgeCsv = (params) => authBlobGet('/admin/knowledge/export/', params)
