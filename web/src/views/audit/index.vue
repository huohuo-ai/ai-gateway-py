<template>
  <div class="audit-page">
    <div class="page-header">
      <h2 class="page-title">审计日志</h2>
      <el-button type="primary" @click="handleExport">
        <el-icon><Download /></el-icon>导出日志
      </el-button>
    </div>
    
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="用户">
          <el-input v-model="searchForm.username" placeholder="用户名" clearable style="width: 150px;" />
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="searchForm.model" placeholder="选择模型" clearable style="width: 150px;">
            <el-option
              v-for="model in models"
              :key="model.model_id"
              :label="model.name"
              :value="model.model_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px;">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 360px;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card shadow="hover">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="log-detail">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="请求ID">{{ row.request_id }}</el-descriptions-item>
                <el-descriptions-item label="IP地址">{{ row.ip_address }}</el-descriptions-item>
                <el-descriptions-item label="User Agent" :span="2">{{ row.user_agent }}</el-descriptions-item>
                <el-descriptions-item label="Prompt Tokens">{{ row.prompt_tokens }}</el-descriptions-item>
                <el-descriptions-item label="Completion Tokens">{{ row.completion_tokens }}</el-descriptions-item>
                <el-descriptions-item label="总Tokens">{{ row.total_tokens }}</el-descriptions-item>
                <el-descriptions-item label="响应时间">{{ row.response_time }}ms</el-descriptions-item>
              </el-descriptions>
              <div class="detail-section" v-if="row.prompt">
                <h4>请求内容</h4>
                <pre class="code-block">{{ truncateText(row.prompt, 500) }}</pre>
              </div>
              <div class="detail-section" v-if="row.response">
                <h4>响应内容</h4>
                <pre class="code-block">{{ truncateText(row.response, 500) }}</pre>
              </div>
              <div class="detail-section" v-if="row.error_message">
                <h4 style="color: #f56c6c;">错误信息</h4>
                <pre class="code-block" style="background: #fef0f0;">{{ row.error_message }}</pre>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="用户" width="120" />
        
        <el-table-column prop="model" label="模型" min-width="150">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.model }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_tokens" label="Tokens" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top">
              <template #content>
                Prompt: {{ row.prompt_tokens }}<br/>
                Completion: {{ row.completion_tokens }}
              </template>
              <span>{{ formatNumber(row.total_tokens) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="response_time" label="响应时间" width="100">
          <template #default="{ row }">
            <span :class="getResponseTimeClass(row.response_time)">
              {{ row.response_time }}ms
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="请求ID">{{ currentLog.request_id }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatTime(currentLog.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item label="模型">{{ currentLog.model }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentLog.status === 'success' ? 'success' : 'danger'" size="small">
            {{ currentLog.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Prompt Tokens">{{ currentLog.prompt_tokens }}</el-descriptions-item>
        <el-descriptions-item label="Completion Tokens">{{ currentLog.completion_tokens }}</el-descriptions-item>
        <el-descriptions-item label="总Tokens">{{ currentLog.total_tokens }}</el-descriptions-item>
        <el-descriptions-item label="响应时间">{{ currentLog.response_time }}ms</el-descriptions-item>
      </el-descriptions>
      
      <div class="detail-section" v-if="currentLog.prompt">
        <h4>请求内容</h4>
        <pre class="code-block">{{ currentLog.prompt }}</pre>
      </div>
      
      <div class="detail-section" v-if="currentLog.response">
        <h4>响应内容</h4>
        <pre class="code-block">{{ currentLog.response }}</pre>
      </div>
      
      <div class="detail-section" v-if="currentLog.error_message">
        <h4 style="color: #f56c6c;">错误信息</h4>
        <pre class="code-block" style="background: #fef0f0;">{{ currentLog.error_message }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Search } from '@element-plus/icons-vue'
import { getAuditLogs, exportAuditLogs } from '@/api/audit'
import { getModels } from '@/api/models'
import dayjs from 'dayjs'

const loading = ref(false)
const logs = ref([])
const models = ref([])
const detailVisible = ref(false)
const currentLog = ref({})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  username: '',
  model: '',
  status: '',
  timeRange: []
})

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getResponseTimeClass = (time) => {
  if (time < 1000) return 'text-success'
  if (time < 3000) return 'text-warning'
  return 'text-danger'
}

const truncateText = (text, length) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

const loadModels = async () => {
  try {
    const res = await getModels({ size: 100 })
    models.value = res.items || []
  } catch (error) {
    models.value = []
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      username: searchForm.username,
      model: searchForm.model,
      status: searchForm.status
    }
    
    if (searchForm.timeRange && searchForm.timeRange.length === 2) {
      params.start_time = searchForm.timeRange[0]
      params.end_time = searchForm.timeRange[1]
    }
    
    const res = await getAuditLogs(params)
    logs.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    // 模拟数据
    logs.value = [
      {
        id: 1,
        request_id: 'req_abc123',
        username: 'admin',
        model: 'gpt-3.5-turbo',
        prompt_tokens: 156,
        completion_tokens: 342,
        total_tokens: 498,
        status: 'success',
        response_time: 1250,
        ip_address: '192.168.1.100',
        created_at: '2024-01-15T10:30:00Z',
        prompt: '你好，请介绍一下自己',
        response: '你好！我是AI助手...'
      },
      {
        id: 2,
        request_id: 'req_def456',
        username: 'user1',
        model: 'gpt-4',
        prompt_tokens: 200,
        completion_tokens: 500,
        total_tokens: 700,
        status: 'success',
        response_time: 2300,
        ip_address: '192.168.1.101',
        created_at: '2024-01-15T11:00:00Z'
      }
    ]
    pagination.total = 2
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadLogs()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.model = ''
  searchForm.status = ''
  searchForm.timeRange = []
  handleSearch()
}

const showDetail = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

const handleExport = async () => {
  try {
    const blob = await exportAuditLogs(searchForm)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_logs_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadModels()
  loadLogs()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-card :deep(.el-card__body) {
  padding-bottom: 0;
}

.log-detail {
  padding: 20px;
  background: #f5f7fa;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}
</style>
