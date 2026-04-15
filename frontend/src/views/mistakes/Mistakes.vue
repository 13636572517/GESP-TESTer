<template>
  <div class="page-container">
    <h1 class="page-title">错题本</h1>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card class="review-card" style="cursor: pointer; height: 100%" @click="handleReview">
          <div style="text-align: center; padding: 12px 0">
            <div style="font-weight: 600; font-size: 16px; color: #21242C">错题复习</div>
            <div style="font-size: 13px; color: #6B7280; margin-top: 6px">自动生成薄弱知识点复习卷</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="18">
        <el-card>
          <template #header>薄弱知识点分布</template>
          <div v-for="item in stats" :key="item.knowledge_id" style="display: flex; align-items: center; justify-content: space-between; padding: 6px 0">
            <span>{{ item.knowledge_name }}</span>
            <el-tag type="danger" size="small">{{ item.mistake_count }} 题</el-tag>
          </div>
          <el-empty v-if="stats.length === 0" description="暂无错题" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>错题列表</span>
          <el-radio-group v-model="filter" size="small" @change="loadMistakes">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="unmastered">未掌握</el-radio-button>
            <el-radio-button value="mastered">已掌握</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div v-for="item in mistakes" :key="item.id" class="mistake-item">
        <div style="display: flex; justify-content: space-between; align-items: flex-start">
          <div style="flex: 1">
            <div v-html="item.question?.content?.substring(0, 150)" style="font-size: 15px"></div>
            <div style="margin-top: 8px; font-size: 13px; color: #6B7280">
              错误 {{ item.wrong_count }} 次 | 连续正确 {{ item.consecutive_correct }} 次
            </div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center; flex-shrink: 0">
            <el-tag :type="item.is_mastered ? 'success' : 'danger'" size="small">
              {{ item.is_mastered ? '已掌握' : '未掌握' }}
            </el-tag>
            <el-button
              v-if="!item.is_mastered"
              class="btn-mastered" size="small"
              @click="handleMastered(item.id)"
            >
              标记掌握
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="mistakes.length === 0" description="暂无错题" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMistakes, getMistakeStats, generateReview, markMastered } from '../../api/practice'

const router = useRouter()
const mistakes = ref([])
const stats = ref([])
const filter = ref('all')

async function loadMistakes() {
  const params = {}
  if (filter.value === 'unmastered') params.mastered = 'false'
  if (filter.value === 'mastered') params.mastered = 'true'
  const res = await getMistakes(params)
  mistakes.value = res.results || res
}

async function handleReview() {
  try {
    const data = await generateReview({ count: 20 })
    sessionStorage.setItem(`practice_${data.session_id}`, JSON.stringify(data.questions))
    router.push(`/practice/${data.session_id}`)
  } catch { /* empty */ }
}

async function handleMastered(id) {
  await markMastered(id)
  ElMessage.success('已标记为掌握')
  loadMistakes()
}

onMounted(async () => {
  loadMistakes()
  try {
    stats.value = await getMistakeStats()
  } catch { /* empty */ }
})
</script>

<style scoped>
.review-card {
  border-left: 4px solid #1865F2 !important;
}
.mistake-item {
  padding: 16px 0;
  border-bottom: 1px solid #E5E7EB;
}
.mistake-item:last-child {
  border-bottom: none;
}
.btn-mastered {
  color: #0D9488 !important;
  background: #E6FAF5 !important;
  border-color: #99E6D8 !important;
  font-size: 12px !important;
  padding: 4px 10px !important;
  height: 26px !important;
  font-weight: 500 !important;
}
.btn-mastered:hover {
  color: #0A7A6E !important;
  background: #CCFAF0 !important;
  border-color: #0D9488 !important;
}
</style>
