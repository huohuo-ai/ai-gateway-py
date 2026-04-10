import request from '@/utils/request'

export const getModelsForChat = () => {
  return request({
    url: '/api/v1/models',
    method: 'get',
    params: { is_active: true }
  })
}

// 流式对话使用 fetch API
export const chatStream = (data, onMessage, onError, onComplete) => {
  const userStore = JSON.parse(localStorage.getItem('user') || '{}')
  const token = userStore.token
  
  fetch('/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      model: data.model,
      messages: data.messages,
      stream: true
    })
  })
    .then(async (response) => {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onComplete && onComplete()
              return
            }
            try {
              const parsed = JSON.parse(data)
              onMessage && onMessage(parsed)
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
      onComplete && onComplete()
    })
    .catch((error) => {
      onError && onError(error)
    })
}
