<template>
  <div class="page-container">
    <h1 class="page-title">模拟考试</h1>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="选择试卷" name="templates">
        <el-row :gutter="16">
          <el-col :span="8" v-for="tpl in templates" :key="tpl.id">
            <el-card shadow="hover" style="margin-bottom: 16px; cursor: pointer; transition: transform 0.2s" @click="handleStartExam(tpl)">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
                <el-tag>{{ tpl.level_name }}</el-tag>
                <el-tag type="info" size="small">{{ tpl.template_type === 1 ? '真题' : '模拟' }}</el-tag>
              </div>
              <h3 style="margin-bottom: 8px">{{ tpl.name }}</h3>
              <div style="color: #909399; font-size: 14px">
                {{ tpl.question_count }} 题 | {{ tpl.duration }} 分钟 | {{ tpl.total_score }} 分
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="templates.length === 0" description="暂无试卷" />

        <el-divider>或者随机组卷</el-divider>
        <el-form :inline="true" :model="randomForm">
          <el-form-item label="级别">
            <el-select v-model="randomForm.level_id" placeholder="选择级别" style="width: 220px">
              <el-option v-for="l in levels" :key="l.id" :label="l.name" :value="l.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <span style="color: #909399; font-size: 13px">15道选择题 + 10道判断题，共25题，60分钟</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleRandomExam">开始随机模考</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="考试记录" name="history">
        <el-table :data="history" stripe>
          <el-table-column prop="template_name" label="试卷" />
          <el-table-column prop="level_name" label="级别" width="100" />
          <el-table-column label="得分" width="120">
            <template #default="{ row }">
              <span :style="{ color: row.earned_score >= (row.total_score * 0.6) ? '#10b981' : '#ef4444', fontWeight: 600 }">
                {{ row.earned_score }} / {{ row.total_score }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'warning'" size="small">
                {{ row.status === 1 ? '已交卷' : '超时交卷' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="切屏" width="80" prop="switch_count" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click="$router.push(`/exam/${row.id}/result`)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExamTemplates, startExam, getExamHistory } from '../../api/exam'
import { getLevels } from '../../api/knowledge'

const router = useRouter()
const activeTab = ref('templates')
const templates = ref([])
const history = ref([])
const levels = ref([])

const randomForm = ref({
  level_id: 1,
})

async function handleStartExam(tpl) {
  await ElMessageBox.confirm(
    `确定开始 "${tpl.name}" 考试？\n时长: ${tpl.duration}分钟，共${tpl.question_count}题`,
    '开始考试',
    { confirmButtonText: '开始', cancelButtonText: '取消' }
  )
  const data = await startExam({ template_id: tpl.id, exam_type: 1 })
  if (data.resume) {
    ElMessage.info('恢复上次未完成的考试')
  }
  router.push(`/exam/${data.record_id}/session`)
}

async function handleRandomExam() {
  const data = await startExam({
    level_id: randomForm.value.level_id,
    exam_type: 2,
  })
  router.push(`/exam/${data.record_id}/session`)
}

onMounted(async () => {
  try {
    const res = await getLevels()
    levels.value = res.results || res
  } catch { /* empty */ }
  try {
    const res = await getExamTemplates()
    templates.value = res.results || res
  } catch { /* empty */ }
  try {
    const res = await getExamHistory()
    history.value = res.results || res
  } catch { /* empty */ }
})
</script>
