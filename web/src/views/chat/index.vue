<template>
  <div class="chat-page">
    <div class="page-header">
      <h2 class="page-title">LLM 对话</h2>
      <el-select v-model="selectedModel" placeholder="选择模型" style="width: 200px;">
        <el-option
          v-for="model in models"
          :key="model.id"
          :label="model.name"
          :value="model.model_id"
        />
      </el-select>
    </div>
    
    <el-card class="chat-container" shadow="hover">
      <div class="chat-messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="chat-empty">
          <el-icon :size="64" color="#dcdfe6"><ChatDotRound /></el-icon>
          <p>开始与 AI 对话</p>
        </div>
        
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <el-avatar
            :size="40"
            :icon="msg.role === 'user' ? UserFilled : Cpu"
            :class="msg.role"
          />
          <div class="message-bubble" :class="msg.role">
            <div class="message-content" v-html="formatMessage(msg.content)"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
        
        <div v-if="loading" class="message-item assistant">
          <el-avatar :size="40" :icon="Cpu" class="assistant" />
          <div class="message-bubble assistant">
            <el-icon class="is-loading"><Loading /></el-icon>
            思考中...
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          resize="none"
          @keyup.enter.ctrl="sendMessage"
        />
        <div class="input-actions">
          <span class="hint">Ctrl + Enter 发送</span>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!inputMessage.trim() || !selectedModel"
            @click="sendMessage"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, UserFilled, Cpu, Loading } from '@element-plus/icons-vue'
import { getModelsForChat, chatStream } from '@/api/chat'
import dayjs from 'dayjs'
import { marked } from 'marked'

const models = ref([])
const selectedModel = ref('')
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref()

// 模拟数据用于演示
const loadModels = async () => {
  try {
    const res = await getModelsForChat()
    models.value = res.items || [
      { id: 1, name: 'GPT-3.5 Turbo', model_id: 'gpt-3.5-turbo' },
      { id: 2, name: 'GPT-4', model_id: 'gpt-4' }
    ]
    if (models.value.length > 0) {
      selectedModel.value = models.value[0].model_id
    }
  } catch (error) {
    // 使用默认数据
    models.value = [
      { id: 1, name: 'GPT-3.5 Turbo', model_id: 'gpt-3.5-turbo' },
      { id: 2, name: 'GPT-4', model_id: 'gpt-4' }
    ]
    selectedModel.value = 'gpt-3.5-turbo'
  }
}

const formatMessage = (content) => {
  return marked(content)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || !selectedModel.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: content,
    time: dayjs().format('HH:mm:ss')
  })
  
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  
  // 添加助手消息占位
  const assistantMsg = {
    role: 'assistant',
    content: '',
    time: dayjs().format('HH:mm:ss')
  }
  messages.value.push(assistantMsg)
  
  try {
    // 模拟流式响应（实际应使用 chatStream）
    await simulateStreamResponse(assistantMsg)
    
    // 实际实现：
    // chatStream(
    //   {
    //     model: selectedModel.value,
    //     messages: messages.value.filter(m => m.role !== 'system').map(m => ({
    //       role: m.role,
    //       content: m.content
    //     }))
    //   },
    //   (chunk) => {
    //     const content = chunk.choices?.[0]?.delta?.content || ''
    //     assistantMsg.content += content
    //     scrollToBottom()
    //   },
    //   (error) => {
    //     ElMessage.error('发送失败：' + error.message)
    //   },
    //   () => {
    //     loading.value = false
    //   }
    // )
  } catch (error) {
    ElMessage.error('发送失败：' + error.message)
    loading.value = false
  }
}

// 模拟流式响应用于演示
const simulateStreamResponse = async (msg) => {
  const responses = [
    '您好！我是AI助手，很高兴为您服务。',
    '我可以帮助您解答问题、生成文本、分析数据等。',
    '请问有什么可以帮您的吗？'
  ]
  
  const response = responses[Math.floor(Math.random() * responses.length)]
  const chars = response.split('')
  
  for (const char of chars) {
    await new Promise(resolve => setTimeout(resolve, 50))
    msg.content += char
    scrollToBottom()
  }
  
  loading.value = false
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 100px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chat-container {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 400px;
  max-height: calc(100vh - 300px);
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.chat-empty p {
  margin-top: 16px;
  font-size: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item .el-avatar {
  flex-shrink: 0;
}

.message-item .el-avatar.user {
  background: #409EFF;
}

.message-item .el-avatar.assistant {
  background: #67C23A;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message-bubble.user {
  background: #409EFF;
  color: white;
}

.message-bubble.assistant {
  background: #f5f7fa;
  color: #303133;
}

.message-content {
  word-break: break-word;
}

.message-content :deep(p) {
  margin: 0 0 8px;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.message-time {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.7;
}

.chat-input {
  border-top: 1px solid #ebeef5;
  padding: 20px;
}

.chat-input .el-textarea {
  margin-bottom: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint {
  font-size: 12px;
  color: #909399;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
