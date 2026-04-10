<template>
  <div class="error-page">
    <div class="error-content">
      <el-icon :size="120" color="#409EFF"><Warning /></el-icon>
      <h1 class="error-code">404</h1>
      <p class="error-message">抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="goHome">
        <el-icon><HomeFilled /></el-icon>
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Warning, HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.error-content {
  text-align: center;
}

.error-code {
  font-size: 72px;
  font-weight: 700;
  color: #303133;
  margin: 24px 0 16px;
}

.error-message {
  font-size: 18px;
  color: #606266;
  margin-bottom: 32px;
}
</style>
