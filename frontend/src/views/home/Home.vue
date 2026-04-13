<template>
  <div class="page-container">
    <h1 class="page-title">学习概览</h1>

    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div :class="['gradient-card', item.color]">
          <div class="card-emoji">{{ item.emoji }}</div>
          <div class="card-value">{{ item.value }}</div>
          <div class="card-label">{{ item.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600">🚀 快捷入口</span>
          </template>
          <div class="quick-links">
            <el-button type="primary" size="large" @click="$router.push('/practice')">
              <el-icon><EditPen /></el-icon> 开始练习
            </el-button>
            <el-button type="success" size="large" @click="$router.push('/exam')">
              <el-icon><Timer /></el-icon> 模拟考试
            </el-button>
            <el-button type="warning" size="large" @click="$router.push('/mistakes')">
              <el-icon><Warning /></el-icon> 错题复习
            </el-button>
            <el-button size="large" @click="$router.push('/knowledge')">
              <el-icon><Collection /></el-icon> 知识点
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600">⚡ 薄弱知识点</span>
          </template>
          <div v-if="weakness.length === 0" style="text-align: center; color: #909399; padding: 20px">
            暂无数据，开始做题后这里会显示你的薄弱知识点
          </div>
          <div v-for="item in weakness" :key="item.knowledge" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0ff">
            <span>{{ item.knowledge_name }}</span>
            <el-tag :type="item.mastery_level <= 1 ? 'danger' : 'warning'" size="small">
              正确率 {{ item.accuracy }}%
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getOverview, getWeakness } from '../../api/stats'

const overview = ref({})
const weakness = ref([])

const statCards = computed(() => [
  { label: '总做题数', value: overview.value.total_practice || 0, emoji: '✏️', color: 'purple' },
  { label: '正确率', value: `${overview.value.accuracy || 0}%`, emoji: '✅', color: 'green' },
  { label: '学习天数', value: overview.value.study_days || 0, emoji: '📅', color: 'orange' },
  { label: '待复习错题', value: overview.value.unmastered_mistakes || 0, emoji: '📝', color: 'pink' },
])

onMounted(async () => {
  try {
    overview.value = await getOverview()
  } catch { /* empty */ }
  try {
    weakness.value = await getWeakness()
  } catch { /* empty */ }
})
</script>

<style scoped>
.quick-links {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.quick-links .el-button {
  width: 100%;
  height: 48px;
  font-size: 15px;
}
</style>
