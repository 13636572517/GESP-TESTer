<template>
  <div class="page-container">
    <h1 class="page-title">学习统计</h1>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="4" v-for="item in statCards" :key="item.label">
        <div :class="['gradient-card', item.color]">
          <div style="text-align: center">
            <div style="font-size: 20px">{{ item.emoji }}</div>
            <div class="card-value" style="font-size: 22px">{{ item.value }}</div>
            <div class="card-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>知识点掌握度</span>
              <el-select v-model="masteryLevel" size="small" placeholder="选择级别" @change="loadMastery">
                <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
              </el-select>
            </div>
          </template>
          <div v-for="item in mastery" :key="item.knowledge" style="margin-bottom: 12px">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px">
              <span style="font-size: 14px">{{ item.knowledge_name }}</span>
              <span style="font-size: 13px; color: #909399">{{ item.accuracy }}%</span>
            </div>
            <el-progress
              :percentage="item.accuracy"
              :color="getMasteryColor(item.mastery_level)"
              :stroke-width="8"
              :show-text="false"
            />
          </div>
          <el-empty v-if="mastery.length === 0" description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>每日学习记录（近30天）</template>
          <div v-for="item in dailyStats" :key="item.study_date" style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f8f8f8">
            <span>{{ item.study_date }}</span>
            <span>做题 {{ item.practice_count }} | 正确 {{ item.correct_count }} | 考试 {{ item.exam_count }}</span>
          </div>
          <el-empty v-if="dailyStats.length === 0" description="暂无数据" :image-size="60" />
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>薄弱知识点 TOP10</template>
          <div v-for="(item, i) in weakness" :key="item.knowledge" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f8f8f8">
            <span>
              <el-tag size="small" type="danger" style="margin-right: 8px">{{ i + 1 }}</el-tag>
              {{ item.knowledge_name }}
            </span>
            <span style="font-size: 13px; color: #f56c6c">正确率 {{ item.accuracy }}%</span>
          </div>
          <el-empty v-if="weakness.length === 0" description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getOverview, getMastery, getDailyStats, getWeakness } from '../../api/stats'

const overview = ref({})
const mastery = ref([])
const dailyStats = ref([])
const weakness = ref([])
const masteryLevel = ref(1)

const statCards = computed(() => [
  { label: '总做题', value: overview.value.total_practice || 0, emoji: '✏️', color: 'purple' },
  { label: '正确率', value: `${overview.value.accuracy || 0}%`, emoji: '✅', color: 'green' },
  { label: '总考试', value: overview.value.total_exams || 0, emoji: '📝', color: 'blue' },
  { label: '学习天数', value: overview.value.study_days || 0, emoji: '📅', color: 'orange' },
  { label: '学习时长', value: `${overview.value.study_minutes || 0}min`, emoji: '⏱️', color: 'teal' },
  { label: '待复习', value: overview.value.unmastered_mistakes || 0, emoji: '📚', color: 'pink' },
])

function getMasteryColor(level) {
  const colors = ['#6b7280', '#ef4444', '#f59e0b', '#6366f1', '#10b981']
  return colors[level] || '#6b7280'
}

async function loadMastery() {
  mastery.value = await getMastery({ level: masteryLevel.value })
}

onMounted(async () => {
  try { overview.value = await getOverview() } catch { /* empty */ }
  loadMastery()
  try { dailyStats.value = await getDailyStats({ days: 30 }) } catch { /* empty */ }
  try { weakness.value = await getWeakness() } catch { /* empty */ }
})
</script>
