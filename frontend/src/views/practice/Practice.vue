<template>
  <div class="page-container">
    <h1 class="page-title">开始练习</h1>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header><span style="font-weight: 600">⚙️ 练习设置</span></template>
          <el-form :model="form" label-width="100px">
            <el-form-item label="练习类型">
              <el-radio-group v-model="form.session_type">
                <el-radio :value="1">知识点专练</el-radio>
                <el-radio :value="2">随机组题</el-radio>
                <el-radio :value="3">错题复习</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="级别">
              <el-select v-model="form.level_id" placeholder="选择级别" clearable>
                <el-option v-for="l in levels" :key="l.id" :label="l.name" :value="l.id" />
              </el-select>
            </el-form-item>

            <el-form-item label="知识点" v-if="form.session_type === 1">
              <el-tree-select
                v-model="form.knowledge_ids"
                :data="treeData"
                multiple
                :render-after-expand="false"
                placeholder="选择知识点"
                check-strictly
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="难度" v-if="form.session_type === 2">
              <el-select v-model="form.difficulty" placeholder="不限" clearable>
                <el-option label="简单" :value="1" />
                <el-option label="中等" :value="2" />
                <el-option label="困难" :value="3" />
              </el-select>
            </el-form-item>

            <el-form-item label="题目数量">
              <el-input-number v-model="form.count" :min="5" :max="100" :step="5" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" size="large" @click="handleStart" :loading="loading" style="height: 48px; font-size: 16px; width: 200px">
                开始练习
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header><span style="font-weight: 600">📋 最近练习</span></template>
          <div v-for="item in history" :key="item.id" style="padding: 8px 0; border-bottom: 1px solid #f0f0f0">
            <div style="display: flex; justify-content: space-between">
              <span style="font-size: 13px; color: #909399">{{ item.created_at }}</span>
              <el-tag size="small" :type="item.accuracy >= 80 ? 'success' : item.accuracy >= 60 ? 'warning' : 'danger'">
                {{ item.accuracy }}%
              </el-tag>
            </div>
            <div style="font-size: 14px; margin-top: 4px">
              {{ item.correct_count }}/{{ item.total_count }} 题
            </div>
          </div>
          <el-empty v-if="history.length === 0" description="暂无记录" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getLevels, getKnowledgeTree } from '../../api/knowledge'
import { startPractice, getPracticeHistory } from '../../api/practice'

const router = useRouter()
const loading = ref(false)
const levels = ref([])
const tree = ref([])
const history = ref([])

const form = ref({
  session_type: 1,
  level_id: null,
  knowledge_ids: [],
  difficulty: null,
  count: 20,
})

const treeData = computed(() => {
  const levelId = form.value.level_id
  const filtered = levelId ? tree.value.filter(l => l.id === levelId) : tree.value
  // Flatten: skip level wrapper, show chapters directly with knowledge points as leaves
  const result = []
  for (const level of filtered) {
    for (const ch of (level.chapters || [])) {
      result.push({
        value: `ch-${ch.id}`,
        label: levelId ? ch.name : `${level.name} - ${ch.name}`,
        children: (ch.points || []).map(p => ({
          value: p.id,
          label: p.name,
        })),
      })
    }
  }
  return result
})

async function handleStart() {
  loading.value = true
  try {
    const payload = { ...form.value }
    // 过滤掉非数字的知识点ID
    if (payload.knowledge_ids) {
      payload.knowledge_ids = payload.knowledge_ids.filter(id => typeof id === 'number')
    }
    const data = await startPractice(payload)
    sessionStorage.setItem(`practice_${data.session_id}`, JSON.stringify(data.questions))
    router.push(`/practice/${data.session_id}`)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await getLevels()
  levels.value = res.results || res
  tree.value = await getKnowledgeTree()
  try {
    const res = await getPracticeHistory({ page_size: 10 })
    history.value = res.results || []
  } catch { /* empty */ }
})
</script>
