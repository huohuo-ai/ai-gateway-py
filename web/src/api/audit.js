import request from '@/utils/request'

export const getAuditLogs = (params) => {
  return request({
    url: '/api/v1/admin/audit-logs',
    method: 'get',
    params
  })
}

export const getAuditStats = (params) => {
  return request({
    url: '/api/v1/admin/audit-stats',
    method: 'get',
    params
  })
}

export const exportAuditLogs = (params) => {
  return request({
    url: '/api/v1/admin/audit-logs/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
