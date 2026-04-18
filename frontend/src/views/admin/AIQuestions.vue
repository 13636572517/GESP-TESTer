<template>
  <div class="page-container">
    <h1 class="page-title">AI 题目工具</h1>

    <el-tabs v-model="activeTab" type="border-card">

      <!-- ── Tab 1：知识点标注 ── -->
      <el-tab-pane label="知识点标注" name="tag">
        <div class="tab-body">
          <el-card shadow="never" class="filter-card">
            <el-form inline>
              <el-form-item label="级别">
                <el-select v-model="tagForm.level" style="width:120px" clearable placeholder="全部级别" @change="loadTagQuestions">
                  <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
                </el-select>
              </el-form-item>
              <el-form-item label="仅显示未标注">
                <el-switch v-model="tagForm.untaggedOnly" @change="loadTagQuestions" />
              </el-form-item>
              <el-form-item>
                <el-button @click="loadTagQuestions" :loading="tagLoading">刷新</el-button>
                <el-button
                  type="primary"
                  :loading="aiTagging"
                  :disabled="tagSelection.length === 0"
                  @click="runAiTag"
                >
                  <span v-if="!aiTagging">AI 批量标注选中 ({{ tagSelection.length }})</span>
                  <span v-else>标注中 {{ aiTagProgress.current }}/{{ aiTagProgress.total }}
                    <template v-if="aiTagProgress.errors > 0">（{{ aiTagProgress.errors }} 失败）</template>
                  </span>
                </el-button>
                <el-button
                  type="success"
                  :disabled="Object.keys(tagResultMap).length === 0"
                  :loading="tagSaving"
                  @click="saveTagResults"
                >
                  保存全部标注结果
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-table
            ref="tagTableRef"
            :data="tagQuestions"
            v-loading="tagLoading"
            @selection-change="rows => tagSelection = rows"
            stripe
            style="margin-top:12px"
          >
            <el-table-column type="selection" width="46" />
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column label="题目内容" min-width="280">
              <template #default="{ row }">
                <div class="q-text-cell">
                  {{ stripHtml(row.content).substring(0, 80) }}
                  <span v-if="stripHtml(row.content).length > 80">…</span>
                </div>
                <el-button link type="primary" size="small" style="padding:0;margin-top:2px" @click.stop="openPreview(row)">查看完整题目</el-button>
              </template>
            </el-table-column>
            <el-table-column label="题型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="当前知识点" min-width="180">
              <template #default="{ row }">
                <el-tag
                  v-for="kpid in (tagResultMap[row.id] ?? row.knowledge_point_ids)"
                  :key="kpid"
                  size="small"
                  type="success"
                  style="margin:2px"
                >{{ kpNameMap[kpid] || kpid }}</el-tag>
                <span v-if="!(tagResultMap[row.id] ?? row.knowledge_point_ids)?.length" style="color:#ccc">未标注</span>
              </template>
            </el-table-column>
            <el-table-column label="AI建议" width="50">
              <template #default="{ row }">
                <el-icon v-if="tagResultMap[row.id]" color="#67c23a"><Check /></el-icon>
              </template>
            </el-table-column>
            <el-table-column label="手动编辑" width="120">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="openEditTag(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ── Tab 2：AI 出题 ── -->
      <el-tab-pane label="AI 出题" name="gen">
        <div class="tab-body">
          <el-card shadow="never" class="filter-card">
            <el-form inline :model="genForm">
              <el-form-item label="级别">
                <el-select v-model="genForm.level" style="width:120px" clearable placeholder="选择级别">
                  <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
                </el-select>
              </el-form-item>
              <el-form-item label="知识点">
                <el-select
                  v-model="genForm.kpId"
                  style="width:240px"
                  filterable
                  clearable
                  placeholder="先选级别，再选知识点"
                  :loading="kpLoading"
                  :disabled="!genForm.level"
                >
                  <el-option-group
                    v-for="ch in genChapters"
                    :key="ch.id"
                    :label="ch.name"
                  >
                    <el-option
                      v-for="kp in ch.points"
                      :key="kp.id"
                      :label="kp.name"
                      :value="kp.id"
                    />
                  </el-option-group>
                </el-select>
              </el-form-item>
              <el-form-item label="题型">
                <el-select v-model="genForm.questionType" style="width:100px">
                  <el-option label="单选题" :value="1" />
                  <el-option label="判断题" :value="3" />
                </el-select>
              </el-form-item>
              <el-form-item label="数量">
                <el-input-number v-model="genForm.count" :min="1" :max="10" style="width:100px" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="genLoading" @click="runGenerate">AI 生成</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 生成结果审核表 -->
          <div v-if="genDrafts.length" style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-weight:600">生成结果（共 {{ genDrafts.length }} 道）— 请审核后保存</span>
              <el-button
                type="success"
                :loading="genSaving"
                :disabled="genSelection.length === 0"
                @click="saveGenDrafts"
              >
                保存选中 ({{ genSelection.length }}) 到题库
              </el-button>
            </div>

            <el-table
              :data="genDrafts"
              @selection-change="rows => genSelection = rows"
              border
            >
              <el-table-column type="selection" width="46" />
              <el-table-column label="题型" width="80">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.question_type === 1 ? '' : 'success'">
                    {{ row.question_type === 1 ? '单选' : '判断' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="难度" width="70">
                <template #default="{ row }">
                  {{ ['','简单','中等','困难'][row.difficulty] }}
                </template>
              </el-table-column>
              <el-table-column label="题目内容" min-width="300">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="genDrafts[$index].content"
                    type="textarea"
                    :rows="3"
                    size="small"
                  />
                </template>
              </el-table-column>
              <el-table-column label="选项/答案" width="220">
                <template #default="{ row, $index }">
                  <template v-if="row.question_type === 1">
                    <div v-for="(opt, oi) in row.options" :key="oi" style="display:flex;gap:4px;margin-bottom:3px">
                      <span style="width:18px;flex-shrink:0">{{ opt.key }}.</span>
                      <el-input v-model="genDrafts[$index].options[oi].text" size="small" />
                    </div>
                    <div style="margin-top:4px">
                      答案：<el-input v-model="genDrafts[$index].answer" size="small" style="width:60px" />
                    </div>
                  </template>
                  <template v-else>
                    答案：
                    <el-radio-group v-model="genDrafts[$index].answer" size="small">
                      <el-radio value="T">正确</el-radio>
                      <el-radio value="F">错误</el-radio>
                    </el-radio-group>
                  </template>
                </template>
              </el-table-column>
              <el-table-column label="解析" min-width="180">
                <template #default="{ row, $index }">
                  <el-input v-model="genDrafts[$index].explanation" type="textarea" :rows="2" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="genDrafts.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else-if="!genLoading" description="填写上方表单后点击「AI 生成」" />
        </div>
      </el-tab-pane>

    </el-tabs>

    <!-- 题目预览弹窗 -->
    <el-dialog v-model="previewVisible" title="题目预览" width="620px" top="8vh">
      <div v-if="previewRow">
        <div class="preview-content" v-html="previewRow.content" />
        <div v-if="previewRow.options?.length" class="preview-options">
          <div v-for="opt in previewRow.options" :key="opt.key" class="preview-option">
            <span class="opt-key">{{ opt.key }}.</span> {{ opt.text }}
          </div>
        </div>
        <el-divider style="margin:12px 0" />
        <div style="font-size:13px;color:#303133">
          <span><strong>答案：</strong>{{ previewRow.answer }}</span>
          <span style="margin-left:24px"><strong>题型：</strong>{{ previewRow.type_display }}</span>
        </div>
        <div v-if="previewRow.explanation" style="margin-top:8px;font-size:13px;color:#606266">
          <strong>解析：</strong>{{ previewRow.explanation }}
        </div>
      </div>
    </el-dialog>

    <!-- 手动编辑知识点标签弹窗 -->
    <el-dialog v-model="editTagVisible" title="编辑知识点标签" width="560px">
      <div v-if="editTagRow">
        <p style="margin-bottom:12px;color:#606266;font-size:13px;line-height:1.6">
          {{ stripHtml(editTagRow.content).substring(0, 120) }}
        </p>
        <div style="margin-bottom:8px;font-size:12px;color:#909399">
          支持跨级别选择知识点；搜索框可快速定位；如确实无法分类请选"其他/无法分类"
        </div>
        <el-select
          v-model="editTagIds"
          multiple
          filterable
          style="width:100%"
          placeholder="选择知识点（可跨级）"
          :loading="editKpLoading"
        >
          <el-option-group
            v-for="ch in editChapters"
            :key="ch._uid"
            :label="`${ch._levelName} · ${ch.name}`"
          >
            <el-option v-for="kp in ch.points" :key="kp.id" :label="kp.name" :value="kp.id" />
          </el-option-group>
        </el-select>
      </div>
      <template #footer>
        <el-button @click="editTagVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditTag">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import {
  getQuestions,
  aiSuggestTagOne, aiConfirmTags, aiGenerateQuestions,
  batchCreateQuestions,
} from '../../api/admin'
import { getChapters } from '../../api/knowledge'

// ─── 公共 ────────────────────────────────────────────
const activeTab = ref('tag')

function stripHtml(html) {
  return html ? html.replace(/<[^>]+>/g, '') : ''
}

// ─── 知识点名称映射（全局用于标签展示）────────────────
const kpNameMap = reactive({})   // { kpId: name }
const genChapters = ref([])      // 章节+知识点树（用于两个 tab 的选择器）
const kpLoading   = ref(false)

async function loadKpTree(level) {
  kpLoading.value = true
  try {
    const data = await getChapters(level)
    const chapters = data.results || data   // 兼容分页和非分页响应
    genChapters.value = chapters
    chapters.forEach(ch => {
      (ch.points || []).forEach(kp => { kpNameMap[kp.id] = kp.name })
    })
  } finally {
    kpLoading.value = false
  }
}

// ─── Tab1：知识点标注 ─────────────────────────────────
const tagForm      = ref({ level: 1, untaggedOnly: true })
const tagLoading   = ref(false)
const aiTagging    = ref(false)
const tagSaving    = ref(false)
const tagQuestions = ref([])
const tagSelection = ref([])
const tagResultMap = reactive({})   // { questionId: [kpId, ...] }  AI 建议结果
const tagTableRef  = ref(null)
const aiTagProgress = ref({ current: 0, total: 0, errors: 0 })

async function loadTagQuestions() {
  tagLoading.value = true
  try {
    // 有选择级别时加载该级别的 KP 树；无级别则跳过（KP 名称在编辑时按需加载）
    if (tagForm.value.level) {
      try { await loadKpTree(tagForm.value.level) } catch { /* KP names optional */ }
    }
    const params = { page_size: 200 }
    if (tagForm.value.level) params.level = tagForm.value.level
    const res = await getQuestions(params)
    let items = res.results || res
    if (tagForm.value.untaggedOnly) {
      items = items.filter(q => !q.knowledge_point_ids?.length)
    }
    tagQuestions.value = items
  } finally {
    tagLoading.value = false
  }
}

async function runAiTag() {
  const questions = [...tagSelection.value]
  if (!questions.length) return

  aiTagging.value = true
  aiTagProgress.value = { current: 0, total: questions.length, errors: 0 }

  for (const q of questions) {
    try {
      const res = await aiSuggestTagOne(q.id)
      if (res.results?.length) {
        // 立即写入 tagResultMap，表格实时更新
        tagResultMap[res.results[0].question_id] = res.results[0].suggested_ids
      } else if (res.errors?.length) {
        aiTagProgress.value.errors++
      }
    } catch {
      aiTagProgress.value.errors++
    }
    aiTagProgress.value.current++
  }

  const ok = aiTagProgress.value.total - aiTagProgress.value.errors
  if (aiTagProgress.value.errors > 0) {
    ElMessage.warning(`标注完成：${ok} 道成功，${aiTagProgress.value.errors} 道失败`)
  } else {
    ElMessage.success(`已完成全部 ${ok} 道题的标注建议，请确认后保存`)
  }
  aiTagging.value = false
}

async function saveTagResults() {
  const payload = Object.entries(tagResultMap).map(([qid, kpids]) => ({
    question_id: Number(qid),
    knowledge_point_ids: kpids,
  }))
  if (!payload.length) return
  tagSaving.value = true
  try {
    const res = await aiConfirmTags(payload)
    ElMessage.success(`已保存 ${res.updated} 道题的知识点标签`)
    // 清空结果，刷新列表
    Object.keys(tagResultMap).forEach(k => delete tagResultMap[k])
    loadTagQuestions()
  } finally {
    tagSaving.value = false
  }
}

// ─── 题目预览弹窗 ─────────────────────────────────────
const previewVisible = ref(false)
const previewRow     = ref(null)

function openPreview(row) {
  previewRow.value  = row
  previewVisible.value = true
}

// ─── 手动编辑标签弹窗（支持跨级选择）────────────────────
const editTagVisible = ref(false)
const editTagRow     = ref(null)
const editTagIds     = ref([])
const editChapters   = ref([])   // 独立于 genChapters，聚合所有级别
const editKpLoading  = ref(false)
let editKpLoaded     = false     // 只加载一次

async function loadEditKpTreeAll() {
  if (editKpLoaded) return
  editKpLoading.value = true
  const all = []
  for (let lvl = 1; lvl <= 8; lvl++) {
    try {
      const data = await getChapters(lvl)
      const chapters = data.results || data
      chapters.forEach(ch => {
        // 注入级别信息，用于分组标签
        all.push({ ...ch, _level: lvl, _levelName: `${lvl}级`, _uid: `${lvl}-${ch.id}` })
        ;(ch.points || []).forEach(kp => { kpNameMap[kp.id] = kp.name })
      })
    } catch { /* 跳过加载失败的级别 */ }
  }
  editChapters.value = all
  editKpLoading.value = false
  editKpLoaded = true
}

function openEditTag(row) {
  editTagRow.value  = row
  editTagIds.value  = [...(tagResultMap[row.id] ?? row.knowledge_point_ids ?? [])]
  loadEditKpTreeAll()   // 首次打开时加载全部级别，之后直接复用
  editTagVisible.value = true
}

function confirmEditTag() {
  tagResultMap[editTagRow.value.id] = [...editTagIds.value]
  editTagVisible.value = false
}

// ─── Tab2：AI 出题 ────────────────────────────────────
const genForm    = ref({ level: 1, kpId: null, questionType: 1, count: 5 })
const genLoading = ref(false)
const genSaving  = ref(false)
const genDrafts  = ref([])
const genSelection = ref([])

// 级别变化时自动刷新知识点列表（watch 比 @change 更可靠，能捕获 clearable 清空）
watch(() => genForm.value.level, (newLevel) => {
  genForm.value.kpId = null
  if (newLevel) {
    loadKpTree(newLevel)
  } else {
    genChapters.value = []
  }
})

async function runGenerate() {
  if (!genForm.value.level) return ElMessage.warning('请选择级别')
  if (!genForm.value.kpId) return ElMessage.warning('请选择知识点')
  genLoading.value = true
  genDrafts.value  = []
  try {
    const res = await aiGenerateQuestions({
      knowledge_point_id: genForm.value.kpId,
      question_type:      genForm.value.questionType,
      count:              genForm.value.count,
    })
    genDrafts.value = res.questions || []
    ElMessage.success(`已生成 ${genDrafts.value.length} 道题，请审核后保存`)
  } finally {
    genLoading.value = false
  }
}

async function saveGenDrafts() {
  if (!genSelection.value.length) return
  genSaving.value = true
  try {
    // 后端期望 { questions: [...] }
    const res = await batchCreateQuestions({ questions: genSelection.value })
    ElMessage.success(`成功保存 ${res.created_count} 道题到题库`)
    // 按对象引用从草稿列表中移除已保存的题
    const savedSet = new Set(genSelection.value)
    genDrafts.value = genDrafts.value.filter(d => !savedSet.has(d))
    genSelection.value = []
  } finally {
    genSaving.value = false
  }
}

onMounted(() => {
  loadKpTree(1)
  loadTagQuestions()
})
</script>

<style scoped>
.tab-body { padding: 4px 0; }
.filter-card { margin-bottom: 0; }
.q-text-cell {
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  word-break: break-all;
}
/* 预览弹窗 */
.preview-content {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  word-break: break-all;
}
.preview-content :deep(pre) {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 13px;
  overflow-x: auto;
}
.preview-content :deep(code) {
  background: #f0f2f5;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
}
.preview-options {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-option {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
}
.opt-key {
  font-weight: 600;
  color: #1865F2;
}
</style>
