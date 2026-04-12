<template>
  <div class="page-container">
    <h1 class="page-title">试卷管理</h1>

    <el-card style="margin-bottom: 16px">
      <el-button type="primary" @click="showCreateDialog">创建试卷</el-button>
    </el-card>

    <el-card>
      <el-table :data="templates" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="试卷名称" />
        <el-table-column prop="level_name" label="级别" width="100" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.template_type === 1 ? '' : 'success'" size="small">
              {{ row.template_type === 1 ? '真题' : '模拟' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question_count" label="题数" width="80" />
        <el-table-column prop="duration" label="时长(分)" width="100" />
        <el-table-column prop="total_score" label="总分" width="80" />
        <el-table-column prop="pass_score" label="及格分" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建试卷弹窗 -->
    <el-dialog v-model="dialogVisible" title="创建试卷" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如 2024年一级真题" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="form.level" @change="loadAvailableQuestions">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.template_type">
            <el-radio :value="1">真题</el-radio>
            <el-radio :value="2">模拟卷</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时长(分)">
          <el-input-number v-model="form.duration" :min="30" :max="180" />
        </el-form-item>
        <el-form-item label="总分">
          <el-input-number v-model="form.total_score" :min="50" :max="200" />
        </el-form-item>
        <el-form-item label="及格分">
          <el-input-number v-model="form.pass_score" :min="30" :max="200" />
        </el-form-item>
        <el-form-item label="选择题目">
          <el-transfer
            v-model="selectedQuestionIds"
            :data="availableQuestions"
            :titles="['可选题目', '已选题目']"
            filterable
            filter-placeholder="搜索题目"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getQuestions } from '../../api/admin'
import { getExamTemplates, createExamTemplate } from '../../api/admin'

const templates = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const availableQuestions = ref([])
const selectedQuestionIds = ref([])

const form = ref({
  name: '',
  level: 1,
  template_type: 1,
  duration: 90,
  total_score: 100,
  pass_score: 60,
})

async function loadTemplates() {
  const res = await getExamTemplates()
  templates.value = res.results || res
}

async function loadAvailableQuestions() {
  const res = await getQuestions({ level: form.value.level, page_size: 500 })
  const items = res.results || res
  availableQuestions.value = items.map(q => ({
    key: q.id,
    label: `[${q.type_display}] ${q.content?.substring(0, 40)}`,
  }))
}

function showCreateDialog() {
  dialogVisible.value = true
  selectedQuestionIds.value = []
  loadAvailableQuestions()
}

async function handleCreate() {
  if (!form.value.name || selectedQuestionIds.value.length === 0) {
    return ElMessage.warning('请填写名称并选择题目')
  }
  saving.value = true
  try {
    const scorePerQ = Math.floor(form.value.total_score / selectedQuestionIds.value.length)
    await createExamTemplate({
      ...form.value,
      question_items: selectedQuestionIds.value.map(id => ({
        question_id: id,
        score: scorePerQ,
      })),
    })
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadTemplates()
  } finally {
    saving.value = false
  }
}

onMounted(loadTemplates)
</script>
