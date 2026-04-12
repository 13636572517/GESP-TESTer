import request from '../utils/request'

export const getOverview = () => request.get('/stats/overview/')
export const getMastery = (params) => request.get('/stats/mastery/', { params })
export const getDailyStats = (params) => request.get('/stats/daily/', { params })
export const getWeakness = () => request.get('/stats/weakness/')
