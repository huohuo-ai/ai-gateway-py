import request from '@/utils/request'

export const getModels = (params) => {
  return request({
    url: '/api/v1/admin/models',
    method: 'get',
    params
  })
}

export const getModel = (id) => {
  return request({
    url: `/api/v1/admin/models/${id}`,
    method: 'get'
  })
}

export const createModel = (data) => {
  return request({
    url: '/api/v1/admin/models',
    method: 'post',
    data
  })
}

export const updateModel = (id, data) => {
  return request({
    url: `/api/v1/admin/models/${id}`,
    method: 'put',
    data
  })
}

export const deleteModel = (id) => {
  return request({
    url: `/api/v1/admin/models/${id}`,
    method: 'delete'
  })
}

export const toggleModelStatus = (id, isActive) => {
  return request({
    url: `/api/v1/admin/models/${id}/status`,
    method: 'patch',
    data: { is_active: isActive }
  })
}
