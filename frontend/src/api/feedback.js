import request from '../utils/request'

export const submitQuestionFeedback = (questionId, data) =>
  request.post(`/questions/${questionId}/feedback/`, data)

export const getAdminFeedbacks = (params) =>
  request.get('/admin/feedbacks/', { params })

export const handleAdminFeedback = (id, data) =>
  request.patch(`/admin/feedbacks/${id}/`, data)
