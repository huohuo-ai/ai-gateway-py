import request from '@/utils/request'

export const getStats = () => {
  return request({
    url: '/api/v1/admin/stats',
    method: 'get'
  })
}

export const getUsageTrend = (params) => {
  return request({
    url: '/api/v1/admin/usage-trend',
    method: 'get',
    params
  })
}

export const getRecentRequests = (params) => {
  return request({
    url: '/api/v1/admin/recent-requests',
    method: 'get',
    params
  })
}

export const getRiskStats = () => {
  return request({
    url: '/api/v1/admin/risk-stats',
    method: 'get'
  })
}
