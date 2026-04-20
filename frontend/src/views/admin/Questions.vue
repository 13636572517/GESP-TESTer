<template>
  <div class="page-container">
    <h1 class="page-title">题目管理</h1>

    <!-- 统计概览 -->
    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="4" v-for="s in levelStats" :key="s.label">
        <el-card shadow="never" body-style="padding: 12px">
          <div style="text-align: center">
            <div style="font-size: 22px; font-weight: 700; color: #1865F2">{{ s.count }}</div>
            <div style="font-size: 12px; color: #6B7280">{{ s.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 + 操作栏 -->
    <el-card style="margin-bottom: 16px">
      <el-form :inline="true" :model="filters">
        <el-form-item label="级别">
          <el-select v-model="filters.level" clearable placeholder="全部" style="width: 100px"
            @change="handleSearch" @clear="handleSearch">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="filters.type" clearable placeholder="全部" style="width: 100px"
            @change="handleSearch" @clear="handleSearch">
            <el-option label="单选题" :value="1" />
            <el-option label="多选题" :value="2" />
            <el-option label="判断题" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="filters.difficulty" clearable placeholder="全部" style="width: 100px"
            @change="handleSearch" @clear="handleSearch">
            <el-option label="简单" :value="1" />
            <el-option label="中等" :value="2" />
            <el-option label="困难" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" clearable placeholder="题目内容关键词" style="width: 180px"
            @keyup.enter="handleSearch" @clear="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider style="margin: 8px 0 12px" />

      <div style="display: flex; justify-content: space-between; align-items: center">
        <div style="display: flex; gap: 8px">
          <el-button type="success" @click="showAddDialog">
            <el-icon><Plus /></el-icon> 新增题目
          </el-button>
          <el-dropdown @command="handleImport">
            <el-button type="warning">
              <el-icon><Upload /></el-icon> 导入 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="csv">CSV文件导入</el-dropdown-item>
                <el-dropdown-item command="json">JSON粘贴导入</el-dropdown-item>
                <el-dropdown-item command="template" divided>下载CSV模板</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-dropdown @command="handleExport">
            <el-button>
              <el-icon><Download /></el-icon> 导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="json">导出为JSON</el-dropdown-item>
                <el-dropdown-item command="csv">导出为CSV</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div>
          <el-button type="danger" :disabled="selectedIds.length === 0" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon> 批量删除 ({{ selectedIds.length }})
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 题目列表 -->
    <el-card>
      <el-table
        ref="tableRef"
        :data="questions"
        stripe
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="level_name" label="级别" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.level_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type_display" label="题型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.question_type === 1 ? '' : row.question_type === 2 ? 'warning' : 'info'">
              {{ row.type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty_display" label="难度" width="70">
          <template #default="{ row }">
            <el-tag size="small" :type="row.difficulty === 1 ? 'success' : row.difficulty === 2 ? 'warning' : 'danger'">
              {{ row.difficulty_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="题目内容" min-width="300">
          <template #default="{ row }">
            <div class="question-preview" @click="showPreviewDialog(row)">
              {{ stripHtml(row.content).substring(0, 80) }}
              <span v-if="row.content?.length > 80">...</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="answer" label="答案" width="70" />
        <el-table-column prop="source" label="来源" width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="176" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 4px; flex-wrap: nowrap">
              <el-button class="op-btn op-preview" size="small" @click="showPreviewDialog(row)">预览</el-button>
              <el-button class="op-btn op-edit" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button class="op-btn op-delete" size="small" @click="handleDelete(row.id)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px">
        <span style="font-size: 13px; color: #6B7280">
          共 {{ total }} 题
        </span>
        <el-pagination
          v-model:current-page="page"
          :page-size="20"
          :total="total"
          layout="prev, pager, next, jumper"
          @current-change="loadQuestions"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑题目' : '新增题目'" width="720px" :close-on-click-modal="false">
      <el-form :model="form" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="级别" required>
              <el-select v-model="form.level" placeholder="选择级别" style="width: 100%">
                <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="题型" required>
              <el-select v-model="form.question_type" style="width: 100%">
                <el-option label="单选题" :value="1" />
                <el-option label="多选题" :value="2" />
                <el-option label="判断题" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度" required>
              <el-select v-model="form.difficulty" style="width: 100%">
                <el-option label="简单" :value="1" />
                <el-option label="中等" :value="2" />
                <el-option label="困难" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题目内容" required>
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="支持HTML格式，如 <pre>代码</pre>" />
        </el-form-item>

        <el-form-item label="选项" v-if="form.question_type !== 3">
          <div v-for="(opt, i) in form.options" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px; width: 100%">
            <el-tag style="flex-shrink: 0; height: 32px; line-height: 32px">{{ opt.key }}</el-tag>
            <el-input v-model="opt.text" placeholder="选项内容" />
            <el-button link type="danger" @click="form.options.splice(i, 1)" v-if="form.options.length > 2">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button size="small" @click="addOption" v-if="form.options.length < 6">
            <el-icon><Plus /></el-icon> 添加选项
          </el-button>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="正确答案" required>
              <el-input v-model="form.answer" placeholder="如 A、AB、T、F" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="来源">
              <el-input v-model="form.source" placeholder="如 2024年GESP一级真题" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="解析">
          <el-input v-model="form.explanation" type="textarea" :rows="3" placeholder="答案解析" />
        </el-form-item>

        <el-form-item label="知识点">
          <el-cascader
            v-model="form.knowledge_point_ids"
            :options="knowledgeTree"
            :props="{ multiple: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
            clearable
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择关联知识点（可多选）"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 题目预览弹窗 -->
    <el-dialog v-model="previewVisible" title="题目预览" width="650px">
      <div v-if="previewQuestion" class="preview-box">
        <div style="display: flex; gap: 8px; margin-bottom: 12px">
          <el-tag>{{ previewQuestion.level_name }}</el-tag>
          <el-tag :type="previewQuestion.question_type === 1 ? '' : previewQuestion.question_type === 2 ? 'warning' : 'info'">
            {{ previewQuestion.type_display }}
          </el-tag>
          <el-tag :type="previewQuestion.difficulty === 1 ? 'success' : previewQuestion.difficulty === 2 ? 'warning' : 'danger'">
            {{ previewQuestion.difficulty_display }}
          </el-tag>
          <el-tag v-if="previewQuestion.source" type="info">{{ previewQuestion.source }}</el-tag>
        </div>

        <div class="preview-content" v-html="previewQuestion.content" v-highlight></div>

        <div class="preview-options" v-if="previewQuestion.question_type !== 3">
          <div v-for="opt in (previewQuestion.options || [])" :key="opt.key" class="preview-option"
            :class="{ correct: previewQuestion.answer?.includes(opt.key) }">
            <span class="opt-key">{{ opt.key }}</span>
            <span v-html="opt.text"></span>
          </div>
        </div>
        <div class="preview-options" v-else>
          <div class="preview-option" :class="{ correct: previewQuestion.answer === 'T' }">
            <span class="opt-key">T</span> 正确
          </div>
          <div class="preview-option" :class="{ correct: previewQuestion.answer === 'F' }">
            <span class="opt-key">F</span> 错误
          </div>
        </div>

        <el-divider />
        <div style="font-size: 14px">
          <div><strong>正确答案：</strong><el-tag type="success" size="small">{{ previewQuestion.answer }}</el-tag></div>
          <div v-if="previewQuestion.explanation" style="margin-top: 8px">
            <strong>解析：</strong>
            <span style="color: #606266">{{ previewQuestion.explanation }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showEditDialog(previewQuestion); previewVisible = false" type="primary">编辑此题</el-button>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- CSV文件导入弹窗 -->
    <el-dialog v-model="csvDialogVisible" title="CSV文件导入" width="550px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <template #title>
          上传CSV格式文件，表头为：级别、题型、难度、题目、选项A~F、答案、解析、来源。
          <el-link type="primary" @click="handleImport('template')" style="margin-left: 4px; cursor: pointer">下载模板</el-link>
        </template>
      </el-alert>

      <el-upload
        ref="csvUploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".csv"
        :on-change="handleCsvFileChange"
        :on-remove="() => csvFile = null"
      >
        <el-icon :size="40" style="color: #6B7280"><UploadFilled /></el-icon>
        <div style="margin-top: 8px">拖拽CSV文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div style="font-size: 12px; color: #6B7280">仅支持 .csv 文件，编码 UTF-8 或 GBK</div>
        </template>
      </el-upload>

      <div v-if="csvResult" style="margin-top: 16px">
        <el-alert :type="csvResult.error_count > 0 ? 'warning' : 'success'" :closable="false">
          <template #title>
            新增 {{ csvResult.created_count }} 题，覆盖更新 {{ csvResult.updated_count ?? 0 }} 题，失败 {{ csvResult.error_count }} 题
          </template>
        </el-alert>
        <div v-if="csvResult.errors?.length > 0" style="margin-top: 8px; max-height: 160px; overflow-y: auto">
          <div v-for="err in csvResult.errors" :key="err.row" style="font-size: 13px; color: #f56c6c; padding: 2px 0">
            第 {{ err.row }} 行: {{ typeof err.errors === 'string' ? err.errors : JSON.stringify(err.errors) }}
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="csvDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleCsvImport" :loading="csvLoading" :disabled="!csvFile">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- JSON粘贴导入弹窗 -->
    <el-dialog v-model="jsonDialogVisible" title="JSON粘贴导入" width="720px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        <template #title>
          粘贴JSON数组格式数据，字段：level(1-8)、question_type(1单选/2多选/3判断)、difficulty(1~3)、content、options、answer、explanation、source
        </template>
      </el-alert>
      <el-input
        v-model="batchJson"
        type="textarea"
        :rows="16"
        placeholder='[
  {
    "level": 1, "question_type": 1, "difficulty": 1,
    "content": "C++中以下哪个是正确的输出语句？",
    "options": [{"key":"A","text":"print()"},{"key":"B","text":"cout<<"},{"key":"C","text":"echo"},{"key":"D","text":"printf"}],
    "answer": "B",
    "explanation": "C++使用cout进行标准输出"
  }
]'
      />
      <div v-if="jsonResult" style="margin-top: 12px">
        <el-alert :type="jsonResult.error_count > 0 ? 'warning' : 'success'" :closable="false">
          <template #title>新增 {{ jsonResult.created_count }} 题，覆盖更新 {{ jsonResult.updated_count ?? 0 }} 题，失败 {{ jsonResult.error_count }} 题</template>
        </el-alert>
        <div v-if="jsonResult.errors?.length > 0" style="margin-top: 8px; max-height: 160px; overflow-y: auto">
          <div v-for="err in jsonResult.errors" :key="err.index" style="font-size: 13px; color: #f56c6c; padding: 2px 0">
            第 {{ err.index + 1 }} 题: {{ JSON.stringify(err.errors) }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="jsonDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleJsonImport" :loading="jsonLoading">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getQuestions, createQuestion, updateQuestion, deleteQuestion,
  batchCreateQuestions, batchDeleteQuestions,
  importCsvQuestions, exportQuestions, downloadCsvTemplate,
} from '../../api/admin'
import { getKnowledgeTree } from '../../api/knowledge'

// === 列表相关 ===
const loading = ref(false)
const questions = ref([])
const total = ref(0)
const page = ref(1)
const selectedIds = ref([])
const tableRef = ref(null)

const filters = ref({ level: null, type: null, difficulty: null, search: '' })

// === 统计 ===
const levelStats = computed(() => {
  const map = {}
  // 只能用当前页+总数做一个简单展示
  return [
    { label: '题目总数', count: total.value },
  ]
})

// === 知识点树 ===
const knowledgeTree = ref([])

// === 新增/编辑弹窗 ===
const saving = ref(false)
const dialogVisible = ref(false)
const editId = ref(null)

const defaultForm = () => ({
  level: 1,
  question_type: 1,
  difficulty: 1,
  content: '',
  options: [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ],
  answer: '',
  explanation: '',
  source: '',
  knowledge_point_ids: [],
})
const form = ref(defaultForm())

// === 预览弹窗 ===
const previewVisible = ref(false)
const previewQuestion = ref(null)

// === CSV导入 ===
const csvDialogVisible = ref(false)
const csvFile = ref(null)
const csvLoading = ref(false)
const csvResult = ref(null)
const csvUploadRef = ref(null)

// === JSON导入 ===
const jsonDialogVisible = ref(false)
const batchJson = ref('')
const jsonLoading = ref(false)
const jsonResult = ref(null)

// ==================== 方法 ====================

function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]+>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
}

async function loadQuestions() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (filters.value.level) params.level = filters.value.level
    if (filters.value.type) params.type = filters.value.type
    if (filters.value.difficulty) params.difficulty = filters.value.difficulty
    if (filters.value.search) params.search = filters.value.search
    const res = await getQuestions(params)
    questions.value = res.results || res
    total.value = res.count || questions.value.length
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadQuestions()
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

// --- 新增 / 编辑 ---
function addOption() {
  const keys = 'ABCDEFGH'
  const next = keys[form.value.options.length]
  if (next) form.value.options.push({ key: next, text: '' })
}

function showAddDialog() {
  editId.value = null
  form.value = defaultForm()
  dialogVisible.value = true
}

function showEditDialog(row) {
  editId.value = row.id
  form.value = {
    level: row.level,
    question_type: row.question_type,
    difficulty: row.difficulty,
    content: row.content,
    options: row.options?.length ? JSON.parse(JSON.stringify(row.options)) : [],
    answer: row.answer,
    explanation: row.explanation || '',
    source: row.source || '',
    knowledge_point_ids: row.knowledge_point_ids || [],
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.content || !form.value.answer) {
    return ElMessage.warning('请填写题目内容和答案')
  }
  saving.value = true
  try {
    if (editId.value) {
      await updateQuestion(editId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createQuestion(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadQuestions()
  } finally {
    saving.value = false
  }
}

// --- 删除 ---
async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除该题目？此操作不可恢复。', '确认删除')
  await deleteQuestion(id)
  ElMessage.success('已删除')
  loadQuestions()
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 道题目？此操作不可恢复。`, '批量删除')
  await batchDeleteQuestions(selectedIds.value)
  ElMessage.success(`已删除 ${selectedIds.value.length} 道题目`)
  selectedIds.value = []
  loadQuestions()
}

// --- 预览 ---
function showPreviewDialog(row) {
  previewQuestion.value = row
  previewVisible.value = true
}

// --- 导入 ---
function handleImport(command) {
  if (command === 'csv') {
    csvFile.value = null
    csvResult.value = null
    csvDialogVisible.value = true
  } else if (command === 'json') {
    jsonResult.value = null
    jsonDialogVisible.value = true
  } else if (command === 'template') {
    triggerBlobDownload(downloadCsvTemplate(), 'import_template.csv')
  }
}

function handleCsvFileChange(uploadFile) {
  csvFile.value = uploadFile.raw
}

async function handleCsvImport() {
  if (!csvFile.value) return ElMessage.warning('请先选择CSV文件')
  csvLoading.value = true
  csvResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', csvFile.value)
    const res = await importCsvQuestions(formData)
    csvResult.value = res
    if (res.created_count > 0) {
      ElMessage.success(`成功导入 ${res.created_count} 道题目`)
      loadQuestions()
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '导入失败')
  } finally {
    csvLoading.value = false
  }
}

async function handleJsonImport() {
  if (!batchJson.value.trim()) return ElMessage.warning('请输入JSON数据')
  let parsed
  try {
    parsed = JSON.parse(batchJson.value)
    if (!Array.isArray(parsed)) return ElMessage.error('JSON数据必须是数组格式')
  } catch {
    return ElMessage.error('JSON格式错误，请检查语法')
  }
  jsonLoading.value = true
  jsonResult.value = null
  try {
    const res = await batchCreateQuestions({ questions: parsed })
    jsonResult.value = res
    if (res.created_count > 0) {
      ElMessage.success(`成功导入 ${res.created_count} 道题目`)
      loadQuestions()
    }
  } catch {
    ElMessage.error('导入失败')
  } finally {
    jsonLoading.value = false
  }
}

// --- 导出 ---
function handleExport(format) {
  const params = { fmt: format }
  if (filters.value.level) params.level = filters.value.level
  if (filters.value.type) params.type = filters.value.type
  if (filters.value.difficulty) params.difficulty = filters.value.difficulty
  const filename = format === 'csv' ? 'questions.csv' : 'questions.json'
  triggerBlobDownload(exportQuestions(params), filename)
}

function triggerBlobDownload(promise, defaultName) {
  promise.then(res => {
    const disposition = res.headers?.['content-disposition'] || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    const filename = match ? match[1] : defaultName
    const url = URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载完成')
  }).catch(() => {
    ElMessage.error('下载失败')
  })
}

// --- 知识点树 ---
async function loadKnowledgeTree() {
  try {
    const tree = await getKnowledgeTree()
    knowledgeTree.value = (tree || []).map(level => ({
      id: `level_${level.id}`,
      name: level.name,
      children: (level.chapters || []).map(ch => ({
        id: `ch_${ch.id}`,
        name: ch.name,
        children: (ch.points || []).map(pt => ({
          id: pt.id,
          name: pt.name,
        })),
      })),
    }))
  } catch { /* empty */ }
}

onMounted(() => {
  loadQuestions()
  loadKnowledgeTree()
})
</script>

<style scoped>
/* 操作列按钮 */
.op-btn {
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
}
.op-preview {
  color: #475569 !important;
  background: #F1F5F9 !important;
  border-color: #CBD5E1 !important;
}
.op-preview:hover {
  color: #1E293B !important;
  background: #E2E8F0 !important;
  border-color: #94A3B8 !important;
}
.op-edit {
  color: #1865F2 !important;
  background: #EBF0FF !important;
  border-color: #B8D1FB !important;
}
.op-edit:hover {
  color: #1551C9 !important;
  background: #D6E4FF !important;
  border-color: #1865F2 !important;
}
.op-delete {
  color: #C0392B !important;
  background: #FEF2F2 !important;
  border-color: #FECACA !important;
}
.op-delete:hover {
  color: #991B1B !important;
  background: #FEE2E2 !important;
  border-color: #F87171 !important;
}

.question-preview {
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
.question-preview:hover {
  color: #1865F2;
}

.preview-box {
  padding: 8px 0;
}
.preview-content {
  font-size: 15px;
  line-height: 1.8;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 16px;
}
.preview-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preview-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  font-size: 14px;
}
.preview-option.correct {
  border-color: #00A60E;
  background: #ecfdf5;
}
.opt-key {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}
.preview-option.correct .opt-key {
  background: #00A60E;
  color: #fff;
}
</style>
