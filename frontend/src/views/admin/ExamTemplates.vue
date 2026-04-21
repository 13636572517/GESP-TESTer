<template>
  <div class="page-container">
    <h1 class="page-title">试卷管理</h1>

    <el-card style="margin-bottom: 16px">
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <el-select v-model="filterLevel" clearable placeholder="全部级别" style="width:110px" @change="loadTemplates">
          <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">创建试卷</el-button>
        <el-button @click="handleExport">导出选中</el-button>
        <el-button @click="handleExportAll">导出全部</el-button>
        <el-button @click="openImportDialog">导入</el-button>
      </div>
    </el-card>

    <!-- 试卷列表 -->
    <el-card>
      <el-table :data="pagedTemplates" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="试卷名称" min-width="160" />
        <el-table-column prop="level_name" label="级别" width="80" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.template_type === 1 ? '' : 'success'" size="small">
              {{ row.template_type === 1 ? '真题' : '模拟' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question_count" label="题数" width="70" />
        <el-table-column prop="duration" label="时长(分)" width="90" />
        <el-table-column prop="total_score" label="总分" width="70" />
        <el-table-column prop="pass_score" label="及格分" width="75" />
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;gap:4px;flex-wrap:nowrap">
              <el-button class="op-btn op-edit" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button
                class="op-btn"
                :class="row.is_active ? 'op-warn' : 'op-success'"
                size="small"
                @click="toggleActive(row)"
              >{{ row.is_active ? '停用' : '启用' }}</el-button>
              <el-popconfirm
                title="确认删除该试卷？删除后不可恢复。"
                confirm-button-text="删除"
                confirm-button-type="danger"
                cancel-button-text="取消"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button class="op-btn op-delete" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="templates.length > pageSize"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="templates.length"
        layout="total, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end; display: flex"
      />
    </el-card>

    <!-- 创建试卷弹窗（全宽大尺寸） -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTemplateId ? '编辑试卷' : '创建试卷'"
      width="92vw"
      :style="{ maxWidth: '1400px' }"
      align-center
      :close-on-click-modal="false"
    >
      <div class="create-body">
        <!-- 基本信息 -->
        <el-card shadow="never" class="section-card">
          <template #header><b>基本信息</b></template>
          <el-form :model="form" label-width="80px" class="basic-form">
            <el-form-item label="名称">
              <el-input v-model="form.name" placeholder="如 2024年一级真题" style="width:260px" />
            </el-form-item>
            <el-form-item label="级别">
              <el-select v-model="form.level" style="width:100px" @change="onLevelChange">
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
              <el-input-number v-model="form.duration" :min="30" :max="180" style="width:130px" />
            </el-form-item>
            <el-form-item label="总分">
              <el-input-number v-model="form.total_score" :min="50" :max="200" style="width:130px" />
            </el-form-item>
            <el-form-item label="及格分">
              <el-input-number v-model="form.pass_score" :min="30" :max="200" style="width:130px" />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 题目双栏选择 -->
        <div class="selector-row">
          <!-- 左栏：可选题目 -->
          <div class="panel left-panel">
            <div class="panel-head">
              <span class="panel-title">可选题目（{{ filteredLeft.length }} 题）</span>
              <div class="filters">
                <el-input
                  v-model="filters.search"
                  placeholder="搜索内容"
                  size="small"
                  clearable
                  style="width:140px"
                />
                <el-select v-model="filters.type" placeholder="题型" size="small" clearable style="width:90px">
                  <el-option label="单选题" :value="1" />
                  <el-option label="多选题" :value="2" />
                  <el-option label="判断题" :value="3" />
                </el-select>
                <el-input
                  v-model="filters.source"
                  placeholder="来源"
                  size="small"
                  clearable
                  style="width:110px"
                />
              </div>
            </div>

            <div class="panel-list">
              <div v-if="loading" class="panel-empty">加载中…</div>
              <template v-else>
                <div
                  v-for="q in filteredLeft"
                  :key="q.id"
                  class="q-item"
                  :class="{ 'q-already': selectedSet.has(q.id) }"
                  @click="toggleLeft(q)"
                >
                  <el-checkbox
                    :model-value="checkedSet.has(q.id)"
                    :disabled="selectedSet.has(q.id)"
                    @change="(v) => onCheckLeft(q.id, v)"
                    @click.stop
                  />
                  <div class="q-body">
                    <div class="q-meta">
                      <el-tag size="small" :type="typeColor(q.question_type)">{{ q.type_display }}</el-tag>
                      <span v-if="q.source" class="q-source">{{ q.source }}</span>
                      <span v-if="selectedSet.has(q.id)" class="q-added">已添加</span>
                    </div>
                    <div class="q-text">{{ q._text?.substring(0, 100) }}</div>
                  </div>
                </div>
                <div v-if="filteredLeft.length === 0" class="panel-empty">暂无符合条件的题目</div>
              </template>
            </div>

            <div class="panel-foot">
              <el-button size="small" @click="checkAll">全选当前</el-button>
              <el-button size="small" @click="checkedSet.clear()">取消勾选</el-button>
              <el-button
                size="small"
                type="primary"
                :disabled="checkedSet.size === 0"
                @click="addChecked"
              >
                添加勾选 ({{ checkedSet.size }}) →
              </el-button>
            </div>
          </div>

          <!-- 右栏：已选题目 -->
          <div class="panel right-panel">
            <div class="panel-head">
              <span class="panel-title">已选题目（{{ selectedQuestions.length }} 题）</span>
              <div style="display:flex;gap:6px">
                <el-button size="small" type="primary" @click="autoSort">一键顺序</el-button>
                <el-button size="small" type="danger" @click="clearSelected">清空</el-button>
              </div>
            </div>

            <div class="panel-list">
              <div
                v-for="(q, idx) in selectedQuestions"
                :key="q.id"
                class="q-item q-selected-item"
              >
                <span class="q-num">{{ idx + 1 }}</span>
                <div class="q-body">
                  <div class="q-meta">
                    <el-tag size="small" :type="typeColor(q.question_type)">{{ q.type_display }}</el-tag>
                    <span v-if="q.source" class="q-source">{{ q.source }}</span>
                  </div>
                  <div class="q-text">{{ q._text?.substring(0, 100) }}</div>
                </div>
                <div class="q-ops">
                  <el-button :icon="ArrowUp" size="small" circle @click="moveUp(idx)" :disabled="idx === 0" />
                  <el-button :icon="ArrowDown" size="small" circle @click="moveDown(idx)" :disabled="idx === selectedQuestions.length - 1" />
                  <el-button :icon="Delete" size="small" circle type="danger" @click="removeQ(idx)" />
                </div>
              </div>
              <div v-if="selectedQuestions.length === 0" class="panel-empty">请从左侧勾选并添加题目</div>
            </div>

            <div class="panel-foot">
              <span class="score-hint" v-if="selectedQuestions.length > 0">
                每题约 <b>{{ scorePerQ }}</b> 分 · 共 {{ selectedQuestions.length }} 题 · 实际总计 {{ scorePerQ * selectedQuestions.length }} 分
              </span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="info"
          :icon="View"
          :disabled="selectedQuestions.length === 0"
          @click="previewVisible = true"
        >
          预览试卷
        </el-button>
        <el-button type="primary" @click="handleCreate" :loading="saving">{{ editingTemplateId ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 试卷预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      title="试卷预览"
      width="780px"
      align-center
    >
      <div class="preview-paper">
        <h2 class="preview-title">{{ form.name || '（未命名）' }}</h2>
        <p class="preview-meta">
          {{ form.level }}级 &nbsp;|&nbsp;
          {{ form.template_type === 1 ? '真题' : '模拟卷' }} &nbsp;|&nbsp;
          考试时长 {{ form.duration }} 分钟 &nbsp;|&nbsp;
          满分 {{ form.total_score }} 分，及格 {{ form.pass_score }} 分
        </p>
        <el-divider />
        <div v-for="(q, idx) in selectedQuestions" :key="q.id" class="pq-block">
          <div class="pq-header">
            <span class="pq-index">{{ idx + 1 }}.</span>
            <el-tag size="small" :type="typeColor(q.question_type)" style="margin:0 6px 0 2px">{{ q.type_display }}</el-tag>
            <span class="pq-score">（{{ scorePerQ }} 分）</span>
            <span v-if="q.source" class="pq-source">来源：{{ q.source }}</span>
          </div>
          <div class="pq-content" v-html="q.content" />
          <div v-if="q.options && q.options.length" class="pq-options">
            <div v-for="(opt, oi) in q.options" :key="oi" class="pq-opt">
              {{ String.fromCharCode(65 + oi) }}. {{ opt }}
            </div>
          </div>
          <el-divider style="margin:12px 0" />
        </div>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入试卷" width="480px">
      <el-alert type="info" :closable="false" style="margin-bottom:14px">
        CSV格式：id, name, level_id, template_type, duration, total_score, pass_score, question_id, score, order<br>
        每行代表一道题，同一试卷的行共享相同的 id/name。已有 id 的试卷将被覆盖更新。
      </el-alert>
      <el-upload :auto-upload="false" :on-change="onImportFileChange" :show-file-list="false" accept=".csv">
        <el-button>选择 CSV 文件</el-button>
      </el-upload>
      <span v-if="importFile" style="margin-left:8px;font-size:12px;color:#6B7280">{{ importFile.name }}</span>
      <div v-if="importResult" style="margin-top:14px">
        <el-alert :type="importResult.error_count > 0 ? 'warning' : 'success'" :closable="false">
          新增 {{ importResult.created_count }} 份，覆盖更新 {{ importResult.updated_count ?? 0 }} 份，失败 {{ importResult.error_count }} 份
        </el-alert>
        <div v-for="err in importResult.errors" :key="err.index" style="font-size:12px;color:#f56c6c;margin-top:4px">
          第 {{ err.index }} 条「{{ err.name }}」：{{ err.error }}
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importing" :disabled="!importFile" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, ArrowUp, ArrowDown, View } from '@element-plus/icons-vue'
import { getQuestions, getExamTemplates, getExamTemplateDetail, createExamTemplate, updateExamTemplate, patchExamTemplate, deleteExamTemplate, exportExamTemplates, importExamTemplates } from '../../api/admin'

// ─── 基础状态 ────────────────────────────────────────
const templates        = ref([])
const filterLevel      = ref(null)
const currentPage      = ref(1)
const pageSize         = 20
const pagedTemplates   = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return templates.value.slice(start, start + pageSize)
})
const dialogVisible    = ref(false)
const previewVisible   = ref(false)
const saving           = ref(false)
const loading          = ref(false)
const editingTemplateId = ref(null)
const allQuestions     = ref([])
const selectedQuestions = ref([])

// ─── 细粒度响应式 Set（Vue 3 原生支持） ─────────────
// 每次 add/delete 只让读过对应 .has(id) 的那一条重渲染，
// 而非重建整个 Set 导致所有条目同时重渲染。
const checkedSet  = reactive(new Set())   // 左栏已勾选
const selectedSet = reactive(new Set())   // 右栏已选中（与 selectedQuestions 保持同步）

// ─── 过滤器 ─────────────────────────────────────────
const filters = ref({ search: '', type: null, source: '' })
const debouncedSearch = ref('')
let _searchTimer = null
watch(() => filters.value.search, val => {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(() => { debouncedSearch.value = val }, 300)
})

// ─── 表单 ───────────────────────────────────────────
const form = ref({
  name: '', level: 1, template_type: 1,
  duration: 90, total_score: 100, pass_score: 60,
})

// ─── 计算属性 ────────────────────────────────────────
const filteredLeft = computed(() => {
  const { type, source } = filters.value
  const search = debouncedSearch.value
  return allQuestions.value.filter(q => {
    if (type   && q.question_type !== type)    return false
    if (source && !q.source?.includes(source)) return false
    if (search && !q._text.includes(search))   return false
    return true
  })
})

const scorePerQ = computed(() => {
  const n = selectedQuestions.value.length
  return n ? Math.floor(form.value.total_score / n) : 0
})

// ─── 辅助 ───────────────────────────────────────────
function stripHtml(html) {
  return html ? html.replace(/<[^>]+>/g, '') : ''
}
function typeColor(t) {
  return t === 1 ? '' : t === 2 ? 'warning' : 'success'
}

// ─── 左栏操作 ────────────────────────────────────────
function onCheckLeft(id, checked) {
  checked ? checkedSet.add(id) : checkedSet.delete(id)
}
function toggleLeft(q) {
  if (selectedSet.has(q.id)) return
  checkedSet.has(q.id) ? checkedSet.delete(q.id) : checkedSet.add(q.id)
}
function checkAll() {
  checkedSet.clear()
  filteredLeft.value.forEach(q => { if (!selectedSet.has(q.id)) checkedSet.add(q.id) })
}
function addChecked() {
  const idMap = new Map(allQuestions.value.map(q => [q.id, q]))
  checkedSet.forEach(id => {
    const q = idMap.get(id)
    if (q && !selectedSet.has(id)) {
      selectedQuestions.value.push(q)
      selectedSet.add(id)
    }
  })
  checkedSet.clear()
}

// ─── 右栏操作 ────────────────────────────────────────
function removeQ(idx) {
  const q = selectedQuestions.value.splice(idx, 1)[0]
  selectedSet.delete(q.id)
}
function clearSelected() {
  selectedQuestions.value = []
  selectedSet.clear()
}
function moveUp(idx) {
  if (idx === 0) return
  const arr = selectedQuestions.value
  ;[arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]]
}
function moveDown(idx) {
  const arr = selectedQuestions.value
  if (idx >= arr.length - 1) return
  ;[arr[idx], arr[idx + 1]] = [arr[idx + 1], arr[idx]]
}
function autoSort() {
  selectedQuestions.value.sort((a, b) => {
    // 1. 选择题(1) 优先于判断题(3)
    if (a.question_type !== b.question_type) return a.question_type - b.question_type
    // 2. 难度升序：简单(1) < 中等(2) < 困难(3)
    if (a.difficulty !== b.difficulty) return a.difficulty - b.difficulty
    // 3. 导入时间升序
    return new Date(a.created_at) - new Date(b.created_at)
  })
}

// ─── 数据加载 ────────────────────────────────────────
async function loadTemplates() {
  const params = { page_size: 1000 }
  if (filterLevel.value) params.level = filterLevel.value
  const res = await getExamTemplates(params)
  templates.value = res.results || res
}

async function loadAvailableQuestions() {
  loading.value = true
  try {
    const res = await getQuestions({ level: form.value.level, page_size: 1000, for_exam: 1 })
    const items = res.results || res
    items.forEach(q => { q._text = stripHtml(q.content) })   // 预计算纯文本，过滤无需重复正则
    allQuestions.value = items
  } finally {
    loading.value = false
  }
}

function onLevelChange() {
  filters.value = { search: '', type: null, source: '' }
  debouncedSearch.value = ''
  checkedSet.clear()
  loadAvailableQuestions()
}

function showCreateDialog() {
  editingTemplateId.value = null
  form.value = { name: '', level: 1, template_type: 1, duration: 90, total_score: 100, pass_score: 60 }
  selectedQuestions.value = []
  selectedSet.clear()
  checkedSet.clear()
  filters.value = { search: '', type: null, source: '' }
  debouncedSearch.value = ''
  dialogVisible.value = true
  loadAvailableQuestions()
}

async function showEditDialog(row) {
  editingTemplateId.value = row.id
  form.value = {
    name: row.name,
    level: row.level,
    template_type: row.template_type,
    duration: row.duration,
    total_score: row.total_score,
    pass_score: row.pass_score,
  }
  selectedQuestions.value = []
  selectedSet.clear()
  checkedSet.clear()
  filters.value = { search: '', type: null, source: '' }
  debouncedSearch.value = ''
  dialogVisible.value = true

  await loadAvailableQuestions()

  const detail = await getExamTemplateDetail(row.id)
  const qMap = new Map(allQuestions.value.map(q => [q.id, q]))
  for (const item of (detail.question_items || [])) {
    const q = qMap.get(item.question_id)
    if (q && !selectedSet.has(q.id)) {
      selectedQuestions.value.push(q)
      selectedSet.add(q.id)
    }
  }
}

// ─── 启用 / 停用 / 删除 ──────────────────────────────
async function toggleActive(row) {
  await patchExamTemplate(row.id, { is_active: !row.is_active })
  row.is_active = !row.is_active
}

async function handleDelete(row) {
  await deleteExamTemplate(row.id)
  ElMessage.success('已删除')
  templates.value = templates.value.filter(t => t.id !== row.id)
}

// ─── 创建提交 ────────────────────────────────────────
async function handleCreate() {
  if (!form.value.name)                return ElMessage.warning('请填写试卷名称')
  if (!selectedQuestions.value.length) return ElMessage.warning('请至少选择一道题目')
  saving.value = true
  try {
    const payload = {
      ...form.value,
      question_items: selectedQuestions.value.map((q, i) => ({
        question_id: q.id, order: i + 1, score: scorePerQ.value,
      })),
    }
    if (editingTemplateId.value) {
      await updateExamTemplate(editingTemplateId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await createExamTemplate(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTemplates()
  } finally {
    saving.value = false
  }
}

// ─── 导出 / 导入 ─────────────────────────────────────
const selectedRows = ref([])
const importDialogVisible = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

function triggerBlobDownload(promise, filename) {
  promise.then(res => {
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载完成')
  }).catch(() => ElMessage.error('下载失败'))
}

function handleExport() {
  const ids = selectedRows.value.map(r => r.id)
  if (!ids.length) return ElMessage.warning('请先勾选要导出的试卷')
  triggerBlobDownload(exportExamTemplates(ids), 'exam_templates.csv')
}

function handleExportAll() {
  triggerBlobDownload(exportExamTemplates([]), 'exam_templates.csv')
}

function openImportDialog() {
  importFile.value = null
  importResult.value = null
  importDialogVisible.value = true
}

function onImportFileChange(file) { importFile.value = file.raw }

async function handleImport() {
  if (!importFile.value) return
  importing.value = true
  importResult.value = null
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await importExamTemplates(fd)
    importResult.value = res
    if (res.created_count > 0 || res.updated_count > 0) {
      ElMessage.success(`新增 ${res.created_count} 份，更新 ${res.updated_count ?? 0} 份`)
      loadTemplates()
    }
  } catch { ElMessage.error('导入失败') } finally { importing.value = false }
}

onMounted(loadTemplates)
</script>

<style scoped>
/* 基本信息表单横排 */
.basic-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0 24px;
}
.basic-form .el-form-item {
  margin-bottom: 12px;
}

/* 双栏选题区 */
.selector-row {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  height: 480px;
}

.panel {
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
}
.left-panel  { flex: 1 1 0; }
.right-panel { flex: 1 1 0; }

.panel-head {
  padding: 10px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.panel-title { font-weight: 600; font-size: 14px; flex-shrink: 0; }

.filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.panel-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.panel-foot {
  padding: 8px 12px;
  background: #f5f7fa;
  border-top: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-empty {
  color: #909399;
  text-align: center;
  padding: 40px 0;
  font-size: 13px;
}

/* 题目行 */
.q-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  gap: 8px;
  transition: background 0.15s;
}
.q-item:hover { background: #f0f7ff; }
.q-already { opacity: 0.45; cursor: default; }
.q-already:hover { background: transparent; }

.q-selected-item { cursor: default; }
.q-selected-item:hover { background: #f0fff4; }

.q-num {
  min-width: 24px;
  font-weight: 600;
  color: #606266;
  font-size: 13px;
  padding-top: 2px;
}

.q-body {
  flex: 1;
  min-width: 0;
}
.q-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.q-source {
  font-size: 11px;
  color: #909399;
  background: #f0f0f0;
  padding: 1px 6px;
  border-radius: 3px;
}
.q-added {
  font-size: 11px;
  color: #67c23a;
}
.q-text {
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
  word-break: break-all;
}

.q-ops {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex-shrink: 0;
}

.score-hint {
  font-size: 13px;
  color: #606266;
}

/* 预览弹窗 */
.preview-paper {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 8px;
}
.preview-title {
  text-align: center;
  font-size: 20px;
  margin: 0 0 8px;
}
.preview-meta {
  text-align: center;
  color: #606266;
  font-size: 13px;
  margin: 0 0 4px;
}
.pq-block { margin-bottom: 4px; }
.pq-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}
.pq-index { font-weight: 700; font-size: 15px; }
.pq-score { color: #909399; font-size: 12px; }
.pq-source { color: #909399; font-size: 12px; margin-left: 8px; }
.pq-content { font-size: 14px; line-height: 1.7; margin-bottom: 6px; }
.pq-options { margin-left: 8px; }
.pq-opt { font-size: 13px; line-height: 1.8; color: #303133; }

.section-card { margin-bottom: 0; }

.op-btn {
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
}
.op-edit {
  color: #1865F2 !important;
  background: #EBF0FF !important;
  border-color: #B8D1FB !important;
}
.op-edit:hover { color: #1551C9 !important; background: #D6E4FF !important; border-color: #1865F2 !important; }
.op-warn {
  color: #B45309 !important;
  background: #FFFBEB !important;
  border-color: #FDE68A !important;
}
.op-warn:hover { color: #92400E !important; background: #FEF3C7 !important; border-color: #F59E0B !important; }
.op-success {
  color: #166534 !important;
  background: #F0FDF4 !important;
  border-color: #BBF7D0 !important;
}
.op-success:hover { color: #14532D !important; background: #DCFCE7 !important; border-color: #4ADE80 !important; }
.op-delete {
  color: #C0392B !important;
  background: #FEF2F2 !important;
  border-color: #FECACA !important;
}
.op-delete:hover { color: #991B1B !important; background: #FEE2E2 !important; border-color: #F87171 !important; }
</style>
