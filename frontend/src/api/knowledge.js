import request from '../utils/request'

export const getLevels = () => request.get('/levels/')
export const getChapters = (levelId) => request.get(`/levels/${levelId}/chapters/`)
export const getKnowledgePoints = (chapterId) => request.get(`/chapters/${chapterId}/points/`)
export const getKnowledgeDetail = (id) => request.get(`/knowledge/${id}/`)
export const getKnowledgeTree = () => request.get('/knowledge/tree/')
