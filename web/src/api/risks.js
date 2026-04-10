import request from '@/utils/request'

export const getRiskAlerts = (params) => {
  return request({
    url: '/api/v1/admin/risk-alerts',
    method: 'get',
    params
  })
}

export const getRiskAlert = (id) => {
  return request({
    url: `/api/v1/admin/risk-alerts/${id}`,
    method: 'get'
  })
}

export const updateRiskStatus = (id, data) => {
  return request({
    url: `/api/v1/admin/risk-alerts/${id}`,
    method: 'patch',
    data
  })
}

export const getRiskRules = () => {
  return request({
    url: '/api/v1/admin/risk-rules',
    method: 'get'
  })
}

export const updateRiskRule = (id, data) => {
  return request({
    url: `/api/v1/admin/risk-rules/${id}`,
    method: 'put',
    data
  })
}
