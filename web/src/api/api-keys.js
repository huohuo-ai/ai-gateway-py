import request from '@/utils/request'

export const getApiKeys = () => {
  return request({
    url: '/api/v1/users/me/api-keys',
    method: 'get'
  })
}

export const createApiKey = (data) => {
  return request({
    url: '/api/v1/users/me/api-keys',
    method: 'post',
    data
  })
}

export const revokeApiKey = (keyId) => {
  return request({
    url: `/api/v1/users/me/api-keys/${keyId}/revoke`,
    method: 'post'
  })
}

export const deleteApiKey = (keyId) => {
  return request({
    url: `/api/v1/users/me/api-keys/${keyId}`,
    method: 'delete'
  })
}
