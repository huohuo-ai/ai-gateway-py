<template>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
    <el-breadcrumb-item v-if="route.meta?.title">
      {{ route.meta.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
:deep(.el-breadcrumb__inner) {
  color: #97a8be;
}

:deep(.el-breadcrumb__inner.is-link:hover) {
  color: #409EFF;
}

:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #606266;
}
</style>
