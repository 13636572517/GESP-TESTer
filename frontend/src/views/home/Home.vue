<template>
  <div class="page-container">
    <h1 class="page-title">学习概览</h1>

    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card">
          <div :class="['stat-icon', item.color]">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600">快捷入口</span>
          </template>
          <div class="quick-links">
            <div class="quick-link-item blue" @click="$router.push('/practice')">
              <el-icon :size="18"><EditPen /></el-icon>
              <span>开始练习</span>
            </div>
            <div class="quick-link-item teal" @click="$router.push('/exam')">
              <el-icon :size="18"><Timer /></el-icon>
              <span>模拟考试</span>
            </div>
            <div class="quick-link-item amber" @click="$router.push('/mistakes')">
              <el-icon :size="18"><Warning /></el-icon>
              <span>错题复习</span>
            </div>
            <div class="quick-link-item slate" @click="$router.push('/knowledge')">
              <el-icon :size="18"><Collection /></el-icon>
              <span>知识点</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="font-weight: 600">薄弱知识点</span>
          </template>
          <div v-if="weakness.length === 0" style="text-align: center; color: #6B7280; padding: 20px">
            暂无数据，开始做题后这里会显示你的薄弱知识点
          </div>
          <div v-for="item in weakness" :key="item.knowledge" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #E5E7EB">
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
  { label: '总做题数', value: overview.value.total_practice || 0, icon: 'EditPen', color: 'blue' },
  { label: '正确率', value: `${overview.value.accuracy || 0}%`, icon: 'CircleCheck', color: 'green' },
  { label: '学习天数', value: overview.value.study_days || 0, icon: 'Calendar', color: 'gold' },
  { label: '待复习错题', value: overview.value.unmastered_mistakes || 0, icon: 'Document', color: 'red' },
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
  gap: 10px;
}
.quick-link-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 52px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: filter 0.15s, transform 0.1s;
  user-select: none;
}
.quick-link-item:hover {
  filter: brightness(0.95);
  transform: translateY(-1px);
}
.quick-link-item:active {
  transform: translateY(0);
  filter: brightness(0.9);
}
.quick-link-item.blue  { background: #EBF4FF; color: #2563EB; }
.quick-link-item.teal  { background: #E6FAF5; color: #0D9488; }
.quick-link-item.amber { background: #FEF9EC; color: #D97706; }
.quick-link-item.slate { background: #F1F5F9; color: #475569; }
</style>
