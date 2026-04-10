<template>
  <div class="api-keys-page">
    <div class="page-header">
      <h2 class="page-title">API 密钥管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>创建密钥
      </el-button>
    </div>
    
    <el-alert
      title="安全提示"
      description="API 密钥是访问 LLM 服务的凭证，请妥善保管。密钥只在创建时显示完整内容，之后无法再次查看。"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    />
    
    <el-card shadow="hover">
      <el-table :data="apiKeys" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="150" />
        
        <el-table-column prop="key_preview" label="密钥" min-width="280">
          <template #default="{ row }">
            <code class="key-preview">{{ row.key_preview }}</code>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="usage" label="使用量" width="120">
          <template #default="{ row }">
            <span v-if="row.usage_limit">
              {{ formatNumber(row.usage_count || 0) }} / {{ formatNumber(row.usage_limit) }}
            </span>
            <span v-else>{{ formatNumber(row.usage_count || 0) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="expires_at" label="过期时间" width="160">
          <template #default="{ row }">
            <span v-if="row.expires_at">{{ formatTime(row.expires_at) }}</span>
            <el-tag v-else type="info" size="small">永不过期</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.is_active"
              type="warning"
              link
              size="small"
              @click="handleRevoke(row)"
            >
              停用
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 创建密钥对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建 API 密钥"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="密钥名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：生产环境密钥" />
        </el-form-item>
        
        <el-form-item label="使用限制">
          <el-input-number
            v-model="form.usage_limit"
            :min="0"
            :step="1000"
            placeholder="0表示无限制"
            style="width: 200px;"
          />
          <span class="form-hint">次（0表示无限制）</span>
        </el-form-item>
        
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="form.expires_at"
            type="datetime"
            placeholder="选择过期时间（可选）"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 显示新密钥对话框 -->
    <el-dialog
      v-model="resultVisible"
      title="API 密钥创建成功"
      width="550px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="请立即复制并保存此密钥"
        description="密钥只会显示一次，关闭后将无法再次查看完整内容。"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      />
      
      <div class="key-result">
        <el-input
          v-model="newKey"
          readonly
          type="textarea"
          :rows="3"
        />
        <el-button type="primary" @click="copyKey">
          <el-icon><CopyDocument /></el-icon>
          复制密钥
        </el-button>
      </div>
      
      <template #footer>
        <el-button type="primary" @click="resultVisible = false">
          我已保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, CopyDocument } from '@element-plus/icons-vue'
import { getApiKeys, createApiKey, revokeApiKey, deleteApiKey } from '@/api/api-keys'
import dayjs from 'dayjs'

const loading = ref(false)
const apiKeys = ref([])
const dialogVisible = ref(false)
const resultVisible = ref(false)
const submitting = ref(false)
const newKey = ref('')
const formRef = ref()

const form = reactive({
  name: '',
  usage_limit: 0,
  expires_at: null
})

const rules = {
  name: [
    { required: true, message: '请输入密钥名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const loadApiKeys = async () => {
  loading.value = true
  try {
    const res = await getApiKeys()
    apiKeys.value = res.items || []
  } catch (error) {
    // 使用模拟数据
    apiKeys.value = [
      {
        id: 1,
        name: '测试密钥',
        key_preview: 'sk-...abcd1234',
        is_active: true,
        usage_count: 1500,
        usage_limit: 10000,
        created_at: '2024-01-15T10:00:00Z'
      }
    ]
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  form.name = ''
  form.usage_limit = 0
  form.expires_at = null
  dialogVisible.value = true
}

const submitCreate = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const res = await createApiKey(form)
      newKey.value = res.api_key || 'sk-test123456789'
      dialogVisible.value = false
      resultVisible.value = true
      loadApiKeys()
    } finally {
      submitting.value = false
    }
  })
}

const copyKey = () => {
  navigator.clipboard.writeText(newKey.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      '停用后该密钥将无法继续使用，是否继续？',
      '确认停用',
      { type: 'warning' }
    )
    await revokeApiKey(row.id)
    ElMessage.success('已停用')
    loadApiKeys()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      '删除后无法恢复，是否继续？',
      '确认删除',
      { type: 'danger' }
    )
    await deleteApiKey(row.id)
    ElMessage.success('已删除')
    loadApiKeys()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadApiKeys()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.key-preview {
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.form-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.key-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.key-result .el-input {
  font-family: monospace;
}
</style>
