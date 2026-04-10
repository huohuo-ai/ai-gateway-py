<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">仪表盘</h2>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.total_requests) }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.total_tokens) }}</div>
            <div class="stat-label">总Token数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fff7e6; color: #fa8c16;">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.active_users) }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fff1f0; color: #f5222d;">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.risk_alerts) }}</div>
            <div class="stat-label">风险告警</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :lg="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>使用趋势</span>
              <el-radio-group v-model="timeRange" size="small" @change="loadTrend">
                <el-radio-button label="7d">近7天</el-radio-button>
                <el-radio-button label="30d">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="trendOption" autoresize />
          </div>
        </el-card>
      </el-col>
      
      <el-col :lg="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>模型使用分布</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="modelOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近请求 -->
    <el-card shadow="hover" class="recent-card">
      <template #header>
        <div class="card-header">
          <span>最近请求</span>
          <el-button type="primary" link @click="$router.push('/audit')">
            查看全部
          </el-button>
        </div>
      </template>
      
      <el-table :data="recentRequests" v-loading="loading">
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="model" label="模型" width="180" />
        <el-table-column prop="prompt_tokens" label="Prompt" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.prompt_tokens) }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_tokens" label="Completion" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.completion_tokens) }}
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
            {{ row.response_time }}ms
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ChatDotRound, Coin, User, Warning } from '@element-plus/icons-vue'
import { getStats, getUsageTrend, getRecentRequests } from '@/api/dashboard'
import dayjs from 'dayjs'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

const loading = ref(false)
const timeRange = ref('7d')

const stats = reactive({
  total_requests: 0,
  total_tokens: 0,
  active_users: 0,
  risk_alerts: 0
})

const recentRequests = ref([])

// 趋势图配置
const trendOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['请求数', 'Token数'],
    bottom: 0
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: []
  },
  yAxis: [
    {
      type: 'value',
      name: '请求数'
    },
    {
      type: 'value',
      name: 'Token数'
    }
  ],
  series: [
    {
      name: '请求数',
      type: 'line',
      smooth: true,
      data: [],
      itemStyle: { color: '#409EFF' }
    },
    {
      name: 'Token数',
      type: 'line',
      smooth: true,
      yAxisIndex: 1,
      data: [],
      itemStyle: { color: '#67C23A' }
    }
  ]
})

// 模型分布图配置
const modelOption = ref({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      data: []
    }
  ]
})

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const loadStats = async () => {
  try {
    const res = await getStats()
    Object.assign(stats, res)
  } catch (error) {
    console.error(error)
  }
}

const loadTrend = async () => {
  try {
    const res = await getUsageTrend({ range: timeRange.value })
    trendOption.value.xAxis.data = res.dates || []
    trendOption.value.series[0].data = res.requests || []
    trendOption.value.series[1].data = res.tokens || []
    
    // 更新模型分布
    modelOption.value.series[0].data = res.model_distribution || []
  } catch (error) {
    console.error(error)
  }
}

const loadRecentRequests = async () => {
  loading.value = true
  try {
    const res = await getRecentRequests({ limit: 10 })
    recentRequests.value = res.items || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadTrend()
  loadRecentRequests()
})
</script>

<style scoped>
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

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-card {
  margin-top: 20px;
}
</style>
