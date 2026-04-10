<template>
  <div class="users-page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>创建用户
      </el-button>
    </div>
    
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="搜索用户名" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="全部角色" clearable style="width: 150px;">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部状态" clearable style="width: 150px;">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
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
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : ''" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quota" label="配额使用情况" min-width="200">
          <template #default="{ row }">
            <div v-if="row.daily_quota" class="quota-bar">
              <div class="quota-info">
                <span>日配额</span>
                <span>{{ formatNumber(row.daily_usage || 0) }} / {{ formatNumber(row.daily_quota) }}</span>
              </div>
              <el-progress
                :percentage="calcPercentage(row.daily_usage, row.daily_quota)"
                :status="getQuotaStatus(row.daily_usage, row.daily_quota)"
              />
            </div>
            <el-tag v-else type="info" size="small">无限制</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="primary" link size="small" @click="handleQuota(row)">
              配额
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
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
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '创建用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确认
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 配额设置对话框 -->
    <el-dialog v-model="quotaVisible" title="设置配额" width="500px">
      <el-form :model="quotaForm" label-width="100px">
        <el-form-item label="日配额">
          <el-input-number v-model="quotaForm.daily_quota" :min="0" :step="1000" style="width: 200px;" />
          <span class="form-hint">Token（0表示无限制）</span>
        </el-form-item>
        <el-form-item label="周配额">
          <el-input-number v-model="quotaForm.weekly_quota" :min="0" :step="10000" style="width: 200px;" />
          <span class="form-hint">Token（0表示无限制）</span>
        </el-form-item>
        <el-form-item label="月配额">
          <el-input-number v-model="quotaForm.monthly_quota" :min="0" :step="50000" style="width: 200px;" />
          <span class="form-hint">Token（0表示无限制）</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="quotaVisible = false">取消</el-button>
        <el-button type="primary" :loading="quotaSubmitting" @click="submitQuota">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getUsers, createUser, updateUser, deleteUser, updateUserQuota } from '@/api/users'
import dayjs from 'dayjs'

const loading = ref(false)
const users = ref([])
const dialogVisible = ref(false)
const quotaVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const quotaSubmitting = ref(false)
const formRef = ref()
const currentUserId = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const searchForm = reactive({
  username: '',
  role: '',
  is_active: ''
})

const form = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true
})

const quotaForm = reactive({
  daily_quota: 0,
  weekly_quota: 0,
  monthly_quota: 0
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '长度在 3 到 32 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
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

const calcPercentage = (used, total) => {
  if (!total) return 0
  return Math.min(Math.round((used / total) * 100), 100)
}

const getQuotaStatus = (used, total) => {
  if (!total) return ''
  const percentage = (used / total) * 100
  if (percentage >= 90) return 'exception'
  if (percentage >= 70) return 'warning'
  return ''
}

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers({
      page: pagination.page,
      size: pagination.size,
      ...searchForm
    })
    users.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    // 模拟数据
    users.value = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        is_active: true,
        daily_quota: 100000,
        daily_usage: 45000,
        created_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        username: 'user1',
        email: 'user1@example.com',
        role: 'user',
        is_active: true,
        daily_quota: 50000,
        daily_usage: 12000,
        created_at: '2024-01-10T10:00:00Z'
      }
    ]
    pagination.total = 2
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.role = ''
  searchForm.is_active = ''
  handleSearch()
}

const resetForm = () => {
  form.id = null
  form.username = ''
  form.email = ''
  form.password = ''
  form.role = 'user'
  form.is_active = true
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  form.id = row.id
  form.username = row.username
  form.email = row.email
  form.role = row.role
  form.is_active = row.is_active
  dialogVisible.value = true
}

const submitForm = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await updateUser(form.id, form)
        ElMessage.success('更新成功')
      } else {
        await createUser(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadUsers()
    } finally {
      submitting.value = false
    }
  })
}

const handleQuota = (row) => {
  currentUserId.value = row.id
  quotaForm.daily_quota = row.daily_quota || 0
  quotaForm.weekly_quota = row.weekly_quota || 0
  quotaForm.monthly_quota = row.monthly_quota || 0
  quotaVisible.value = true
}

const submitQuota = async () => {
  quotaSubmitting.value = true
  try {
    await updateUserQuota(currentUserId.value, quotaForm)
    ElMessage.success('配额设置成功')
    quotaVisible.value = false
    loadUsers()
  } finally {
    quotaSubmitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadUsers()
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

.quota-bar {
  min-width: 180px;
}

.quota-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.form-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
