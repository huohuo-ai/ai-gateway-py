import request from '@/utils/request'

export const login = (data) => {
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    data
  })
}

export const getUserInfo = () => {
  return request({
    url: '/api/v1/users/me',
    method: 'get'
  })
}

export const changePassword = (data) => {
  return request({
    url: '/api/v1/users/me/password',
    method: 'put',
    data
  })
}
