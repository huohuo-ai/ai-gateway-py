<template>
  <div class="models-page">
    <div class="page-header">
      <h2 class="page-title">AI 模型管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>添加模型
      </el-button>
    </div>
    
    <el-card shadow="hover">
      <el-table :data="models" v-loading="loading" stripe>
        <el-table-column prop="name" label="模型名称" min-width="150" />
        
        <el-table-column prop="model_id" label="模型ID" min-width="180">
          <template #default="{ row }">
            <code>{{ row.model_id }}</code>
          </template>
        </el-table-column>
        
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">
              {{ row.provider }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="(val) => toggleStatus(row, val)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="max_tokens" label="最大Token" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.max_tokens) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="cost_per_1k" label="单价" width="150">
          <template #default="{ row }">
            <div class="cost-info">
              <span>输入: ${{ row.input_cost_per_1k }}/1K</span>
              <span>输出: ${{ row.output_cost_per_1k }}/1K</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="loadModels"
          @current-change="loadModels"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模型' : '添加模型'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：GPT-4" />
        </el-form-item>
        
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="form.model_id" placeholder="例如：gpt-4" />
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%;">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API基础URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="输入API密钥"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大Token数" prop="max_tokens">
              <el-input-number v-model="form.max_tokens" :min="1" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度" prop="temperature">
              <el-input-number
                v-model="form.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="输入单价" prop="input_cost_per_1k">
              <el-input-number
                v-model="form.input_cost_per_1k"
                :min="0"
                :precision="4"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="输出单价" prop="output_cost_per_1k">
              <el-input-number
                v-model="form.output_cost_per_1k"
                :min="0"
                :precision="4"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="3"
            placeholder="可选：设置默认系统提示词"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="模型描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getModels, createModel, updateModel, deleteModel, toggleModelStatus } from '@/api/models'
import dayjs from 'dayjs'

const loading = ref(false)
const models = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const form = reactive({
  id: null,
  name: '',
  model_id: '',
  provider: 'openai',
  base_url: '',
  api_key: '',
  max_tokens: 4096,
  temperature: 0.7,
  input_cost_per_1k: 0,
  output_cost_per_1k: 0,
  system_prompt: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入API基础URL', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }]
}

const formatNumber = (num) => {
  if (!num) return '-'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const loadModels = async () => {
  loading.value = true
  try {
    const res = await getModels({
      page: pagination.page,
      size: pagination.size
    })
    models.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    // 模拟数据
    models.value = [
      {
        id: 1,
        name: 'GPT-3.5 Turbo',
        model_id: 'gpt-3.5-turbo',
        provider: 'openai',
        is_active: true,
        max_tokens: 4096,
        input_cost_per_1k: 0.0015,
        output_cost_per_1k: 0.002,
        description: 'OpenAI GPT-3.5 Turbo 模型',
        created_at: '2024-01-10T08:00:00Z'
      },
      {
        id: 2,
        name: 'GPT-4',
        model_id: 'gpt-4',
        provider: 'openai',
        is_active: true,
        max_tokens: 8192,
        input_cost_per_1k: 0.03,
        output_cost_per_1k: 0.06,
        description: 'OpenAI GPT-4 模型',
        created_at: '2024-01-15T10:00:00Z'
      }
    ]
    pagination.total = 2
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.id = null
  form.name = ''
  form.model_id = ''
  form.provider = 'openai'
  form.base_url = ''
  form.api_key = ''
  form.max_tokens = 4096
  form.temperature = 0.7
  form.input_cost_per_1k = 0
  form.output_cost_per_1k = 0
  form.system_prompt = ''
  form.description = ''
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, row)
  dialogVisible.value = true
}

const submitForm = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await updateModel(form.id, form)
        ElMessage.success('更新成功')
      } else {
        await createModel(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadModels()
    } finally {
      submitting.value = false
    }
  })
}

const toggleStatus = async (row, val) => {
  try {
    await toggleModelStatus(row.id, val)
    ElMessage.success(val ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !val
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${row.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteModel(row.id)
    ElMessage.success('删除成功')
    loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.cost-info {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  gap: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
