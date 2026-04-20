<template>
  <div class="page-container">
    <h1 class="page-title">编程题管理</h1>

    <!-- 操作栏 -->
    <el-card style="margin-bottom: 16px">
      <el-form inline>
        <el-form-item label="级别">
          <el-select v-model="filterLevel" clearable placeholder="全部" style="width:100px" @change="load">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="openCreate">新增编程题</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 题目列表 -->
    <el-card v-loading="loading">
      <el-empty v-if="!loading && questions.length === 0" description="暂无编程题" />
      <el-table v-else :data="questions" style="width:100%">
        <el-table-column label="ID" prop="id" width="60" />
        <el-table-column label="标题" prop="title" />
        <el-table-column label="级别" width="70">
          <template #default="{ row }">{{ row.level_id }}级</template>
        </el-table-column>
        <el-table-column label="难度" width="80">
          <template #default="{ row }">
            <el-tag :type="diffType(row.difficulty)" size="small">{{ row.difficulty_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="90">
          <template #default="{ row }">{{ row.time_limit }}ms</template>
        </el-table-column>
        <el-table-column label="内存" width="90">
          <template #default="{ row }">{{ row.memory_limit }}MB</template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openTestCases(row)">测试点</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑编程题' : '新增编程题'" width="700px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="标题">
              <el-input v-model="form.title" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="级别">
              <el-select v-model="form.level_id" style="width:100%">
                <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option label="简单" :value="1" />
                <el-option label="中等" :value="2" />
                <el-option label="困难" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时间限制(ms)">
              <el-input-number v-model="form.time_limit" :min="100" :max="10000" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="内存(MB)">
              <el-input-number v-model="form.memory_limit" :min="16" :max="512" :step="16" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="5" placeholder="支持Markdown" />
        </el-form-item>
        <el-form-item label="输入说明">
          <el-input v-model="form.input_description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="输出说明">
          <el-input v-model="form.output_description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试点管理对话框 -->
    <el-dialog v-model="tcVisible" :title="`测试点管理 - ${currentQuestion?.title}`" width="800px">
      <div style="margin-bottom:12px">
        <el-button type="primary" size="small" @click="addTestCase">添加测试点</el-button>
      </div>
      <el-table :data="testCases" style="width:100%">
        <el-table-column label="输入" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.input_data" type="textarea" :rows="2" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="期望输出" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.expected_output" type="textarea" :rows="2" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="样例" width="70">
          <template #default="{ row }">
            <el-checkbox v-model="row.is_sample" />
          </template>
        </el-table-column>
        <el-table-column label="" width="60">
          <template #default="{ $index }">
            <el-button size="small" type="danger" link @click="testCases.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="tcVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingTc" @click="handleSaveTestCases">保存测试点</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const loading = ref(false)
const saving = ref(false)
const savingTc = ref(false)
const questions = ref([])
const filterLevel = ref(null)

const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref(defaultForm())

const tcVisible = ref(false)
const currentQuestion = ref(null)
const testCases = ref([])

function defaultForm() {
  return { title: '', level_id: 1, difficulty: 1, time_limit: 1000, memory_limit: 256, description: '', input_description: '', output_description: '' }
}

function diffType(d) { return { 1: 'success', 2: 'warning', 3: 'danger' }[d] ?? '' }

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filterLevel.value) params.level = filterLevel.value
    questions.value = await request.get('/admin/programming/questions/', { params })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = defaultForm()
  dialogVisible.value = true
}

async function openEdit(row) {
  editingId.value = row.id
  const data = await request.get(`/admin/programming/questions/${row.id}/`)
  form.value = {
    title: data.title,
    level_id: data.level_id,
    difficulty: data.difficulty,
    time_limit: data.time_limit,
    memory_limit: data.memory_limit,
    description: data.description,
    input_description: data.input_description,
    output_description: data.output_description,
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.title.trim()) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    if (editingId.value) {
      await request.put(`/admin/programming/questions/${editingId.value}/`, form.value)
    } else {
      await request.post('/admin/programming/questions/', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除"${row.title}"？`, '提示', { type: 'warning' })
  await request.delete(`/admin/programming/questions/${row.id}/`)
  ElMessage.success('已删除')
  load()
}

async function openTestCases(row) {
  currentQuestion.value = row
  const data = await request.get(`/admin/programming/questions/${row.id}/`)
  testCases.value = data.test_cases.map(tc => ({ ...tc }))
  tcVisible.value = true
}

function addTestCase() {
  testCases.value.push({ input_data: '', expected_output: '', is_sample: false })
}

async function handleSaveTestCases() {
  savingTc.value = true
  try {
    await request.post(`/admin/programming/questions/${currentQuestion.value.id}/test-cases/`, {
      test_cases: testCases.value,
    })
    ElMessage.success('测试点已保存')
    tcVisible.value = false
  } finally {
    savingTc.value = false
  }
}

onMounted(load)
</script>
