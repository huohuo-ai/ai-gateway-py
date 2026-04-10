<template>
  <el-dialog
    v-model="visible"
    title="修改密码"
    width="450px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="原密码" prop="old_password">
        <el-input
          v-model="form.old_password"
          type="password"
          show-password
          placeholder="请输入原密码"
        />
      </el-form-item>
      
      <el-form-item label="新密码" prop="new_password">
        <el-input
          v-model="form.new_password"
          type="password"
          show-password
          placeholder="请输入新密码"
        />
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input
          v-model="form.confirm_password"
          type="password"
          show-password
          placeholder="请再次输入新密码"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确认
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'

const visible = ref(false)
const loading = ref(false)
const formRef = ref()

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const open = () => {
  visible.value = true
  form.old_password = ''
  form.new_password = ''
  form.confirm_password = ''
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await changePassword({
        old_password: form.old_password,
        new_password: form.new_password
      })
      ElMessage.success('密码修改成功，请重新登录')
      visible.value = false
    } finally {
      loading.value = false
    }
  })
}

defineExpose({ open })
</script>
