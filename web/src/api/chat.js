import request from '@/utils/request'
import Cookies from 'js-cookie'

export const getModelsForChat = () => {
  return request({
    url: '/api/v1/models',
    method: 'get',
    params: { is_active: true }
  })
}

// Unified chat completion handler (supports both streaming and non-streaming)
export const chatStream = (data, onMessage, onError, onComplete) => {
  const token = Cookies.get('ai_gateway_token')

  fetch('/api/v1/chat/completions', {
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
      const contentType = response.headers.get('content-type') || ''

      // Non-streaming JSON response (e.g. audit-analyzer)
      if (contentType.includes('application/json')) {
        const json = await response.json()
        const content = json.choices?.[0]?.message?.content || json.choices?.[0]?.delta?.content || ''
        if (content) {
          // Simulate chunk-by-chunk for consistent UI behavior
          const chars = content.split('')
          let index = 0
          const emitNext = () => {
            if (index >= chars.length) {
              onComplete && onComplete()
              return
            }
            // Emit a small batch of chars at a time
            const batch = chars.slice(index, index + 5).join('')
            index += 5
            onMessage && onMessage({ choices: [{ delta: { content: batch } }] })
            setTimeout(emitNext, 8)
          }
          emitNext()
        } else {
          onComplete && onComplete()
        }
        return
      }

      // SSE streaming response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (dataStr === '[DONE]') {
              onComplete && onComplete()
              return
            }
            try {
              const parsed = JSON.parse(dataStr)
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
