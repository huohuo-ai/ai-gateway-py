<template>
  <div class="risks-page">
    <div class="page-header">
      <h2 class="page-title">风险告警</h2>
      <el-button type="primary" @click="showRules = true">
        <el-icon><Setting /></el-icon>告警规则
      </el-button>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.high }}</div>
            <div class="stat-label">高风险</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.medium }}</div>
            <div class="stat-label">中风险</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f4f4f5; color: #909399;">
            <el-icon><InfoFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.low }}</div>
            <div class="stat-label">低风险</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f0f9eb; color: #67c23a;">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.resolved }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="风险类型">
          <el-select v-model="searchForm.risk_type" placeholder="全部类型" clearable style="width: 150px;">
            <el-option label="Token滥用" value="token_abuse" />
            <el-option label="非工作时间访问" value="off_hours" />
            <el-option label="异常频率" value="abnormal_frequency" />
            <el-option label="IP异常" value="ip_anomaly" />
            <el-option label="提示词注入" value="prompt_injection" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="searchForm.severity" placeholder="全部等级" clearable style="width: 150px;">
            <el-option label="高风险" value="high" />
            <el-option label="中风险" value="medium" />
            <el-option label="低风险" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px;">
            <el-option label="未处理" value="new" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已忽略" value="ignored" />
          </el-select>
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
      <el-table :data="alerts" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="severity" label="等级" width="90">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="risk_type" label="类型" width="140">
          <template #default="{ row }">
            {{ getRiskTypeLabel(row.risk_type) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="用户" width="120" />
        
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="handled_by" label="处理人" width="120">
          <template #default="{ row }">
            {{ row.handled_by || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'new'"
              type="primary"
              link
              size="small"
              @click="handleStatus(row, 'processing')"
            >
              标记处理
            </el-button>
            <el-button
              v-if="row.status === 'processing'"
              type="success"
              link
              size="small"
              @click="handleStatus(row, 'resolved')"
            >
              解决
            </el-button>
            <el-button type="primary" link size="small" @click="showDetail(row)">
              详情
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
          @size-change="loadAlerts"
          @current-change="loadAlerts"
        />
      </div>
    </el-card>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="风险告警详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="告警ID">{{ currentAlert.id }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatTime(currentAlert.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="getSeverityType(currentAlert.severity)" size="small">
            {{ getSeverityLabel(currentAlert.severity) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="风险类型">
          {{ getRiskTypeLabel(currentAlert.risk_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentAlert.username }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentAlert.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="处理状态">
          <el-tag :type="getStatusType(currentAlert.status)" size="small">
            {{ getStatusLabel(currentAlert.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentAlert.handled_by || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div class="detail-section">
        <h4>风险描述</h4>
        <p>{{ currentAlert.description }}</p>
      </div>
      
      <div class="detail-section" v-if="currentAlert.evidence">
        <h4>证据数据</h4>
        <pre class="code-block">{{ JSON.stringify(currentAlert.evidence, null, 2) }}</pre>
      </div>
      
      <div class="detail-section" v-if="currentAlert.suggestion">
        <h4>处理建议</h4>
        <el-alert :title="currentAlert.suggestion" type="info" :closable="false" />
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="currentAlert.status === 'new'"
          type="primary"
          @click="handleStatus(currentAlert, 'processing')"
        >
          标记处理中
        </el-button>
        <el-button
          v-if="currentAlert.status === 'processing'"
          type="success"
          @click="handleStatus(currentAlert, 'resolved')"
        >
          标记已解决
        </el-button>
        <el-button
          v-if="currentAlert.status !== 'ignored' && currentAlert.status !== 'resolved'"
          type="info"
          @click="handleStatus(currentAlert, 'ignored')"
        >
          忽略
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 规则设置对话框 -->
    <el-dialog v-model="showRules" title="告警规则设置" width="700px">
      <el-table :data="rules" stripe>
        <el-table-column prop="name" label="规则名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="updateRule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" width="150">
          <template #default="{ row }">
            <el-input-number
              v-if="row.threshold !== undefined"
              v-model="row.threshold"
              :min="0"
              size="small"
              style="width: 100px;"
              @change="updateRule(row)"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, Bell, InfoFilled, CircleCheck, Setting, Search } from '@element-plus/icons-vue'
import { getRiskAlerts, getRiskAlert, updateRiskStatus, getRiskRules, updateRiskRule } from '@/api/risks'
import dayjs from 'dayjs'

const loading = ref(false)
const alerts = ref([])
const rules = ref([])
const detailVisible = ref(false)
const showRules = ref(false)
const currentAlert = ref({})

const stats = reactive({
  high: 0,
  medium: 0,
  low: 0,
  resolved: 0
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  risk_type: '',
  severity: '',
  status: ''
})

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getSeverityType = (severity) => {
  const map = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const map = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return map[severity] || severity
}

const getRiskTypeLabel = (type) => {
  const map = {
    token_abuse: 'Token滥用',
    off_hours: '非工作时间访问',
    abnormal_frequency: '异常频率',
    ip_anomaly: 'IP异常',
    prompt_injection: '提示词注入',
    sensitive_data: '敏感数据获取'
  }
  return map[type] || type
}

const getStatusType = (status) => {
  const map = {
    new: 'danger',
    processing: 'warning',
    resolved: 'success',
    ignored: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = {
    new: '未处理',
    processing: '处理中',
    resolved: '已解决',
    ignored: '已忽略'
  }
  return map[status] || status
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const res = await getRiskAlerts({
      page: pagination.page,
      size: pagination.size,
      ...searchForm
    })
    alerts.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    // 模拟数据
    alerts.value = [
      {
        id: 1,
        severity: 'high',
        risk_type: 'token_abuse',
        username: 'user1',
        description: '用户1小时内Token使用量超过阈值 (150000 > 100000)',
        status: 'new',
        ip_address: '192.168.1.100',
        created_at: '2024-01-15T14:30:00Z',
        suggestion: '建议暂时限制该用户的API访问权限，联系用户确认是否有异常使用情况。'
      },
      {
        id: 2,
        severity: 'medium',
        risk_type: 'off_hours',
        username: 'user2',
        description: '用户在非工作时间 (02:15) 访问API',
        status: 'processing',
        handled_by: 'admin',
        ip_address: '192.168.1.101',
        created_at: '2024-01-15T02:15:00Z',
        suggestion: '确认是否为用户的正常业务操作。'
      }
    ]
    pagination.total = 2
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  // 从数据计算统计
  stats.high = alerts.value.filter(a => a.severity === 'high' && a.status !== 'resolved').length
  stats.medium = alerts.value.filter(a => a.severity === 'medium' && a.status !== 'resolved').length
  stats.low = alerts.value.filter(a => a.severity === 'low' && a.status !== 'resolved').length
  stats.resolved = alerts.value.filter(a => a.status === 'resolved').length
}

const loadRules = async () => {
  try {
    const res = await getRiskRules()
    rules.value = res || []
  } catch (error) {
    rules.value = [
      { name: 'Token滥用检测', description: '检测用户Token使用量是否超过阈值', enabled: true, threshold: 100000 },
      { name: '非工作时间访问', description: '检测用户在非工作时间访问API', enabled: true },
      { name: '异常频率检测', description: '检测用户请求频率是否异常', enabled: true, threshold: 100 },
      { name: 'IP异常检测', description: '检测来自异常IP的访问', enabled: true },
      { name: '提示词注入检测', description: '检测潜在的提示词注入攻击', enabled: true }
    ]
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadAlerts()
}

const handleReset = () => {
  searchForm.risk_type = ''
  searchForm.severity = ''
  searchForm.status = ''
  handleSearch()
}

const showDetail = async (row) => {
  try {
    const res = await getRiskAlert(row.id)
    currentAlert.value = res || row
  } catch (error) {
    currentAlert.value = row
  }
  detailVisible.value = true
}

const handleStatus = async (row, status) => {
  try {
    await updateRiskStatus(row.id, { status })
    ElMessage.success('状态更新成功')
    loadAlerts()
    if (detailVisible.value) {
      detailVisible.value = false
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const updateRule = async (row) => {
  try {
    await updateRiskRule(row.id, { enabled: row.enabled, threshold: row.threshold })
    ElMessage.success('规则更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

onMounted(() => {
  loadAlerts()
  loadRules()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.search-card {
  margin-bottom: 20px;
}

.search-card :deep(.el-card__body) {
  padding-bottom: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 12px;
  color: #303133;
}
</style>
