import request from '@/utils/request'

export const getUsers = (params) => {
  return request({
    url: '/api/v1/admin/users',
    method: 'get',
    params
  })
}

export const getUser = (id) => {
  return request({
    url: `/api/v1/admin/users/${id}`,
    method: 'get'
  })
}

export const createUser = (data) => {
  return request({
    url: '/api/v1/admin/users',
    method: 'post',
    data
  })
}

export const updateUser = (id, data) => {
  return request({
    url: `/api/v1/admin/users/${id}`,
    method: 'put',
    data
  })
}

export const deleteUser = (id) => {
  return request({
    url: `/api/v1/admin/users/${id}`,
    method: 'delete'
  })
}

export const updateUserQuota = (id, data) => {
  return request({
    url: `/api/v1/admin/users/${id}/quota`,
    method: 'put',
    data
  })
}

export const resetUserPassword = (id, data) => {
  return request({
    url: `/api/v1/admin/users/${id}/reset-password`,
    method: 'post',
    data
  })
}
