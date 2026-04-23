<template>
  <div class="page-container">
    <h1 class="page-title">PDF 试卷导入</h1>

    <!-- Step 1: 上传配置 -->
    <el-card v-if="step === 1" style="max-width: 600px; margin: 0 auto">
      <template #header><span style="font-weight:600">上传 GESP 试卷 PDF</span></template>

      <el-form label-width="90px" style="margin-top: 8px">
        <el-form-item label="试卷级别">
          <el-select v-model="level" style="width: 140px">
            <el-option v-for="i in 8" :key="i" :label="`GESP ${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源描述">
          <el-input v-model="source" placeholder="如：2024年12月一级真题" style="width: 300px" />
        </el-form-item>
        <el-form-item label="PDF 文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".pdf"
            :on-change="handleFileChange"
            :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            drag
            style="width: 360px"
          >
            <el-icon style="font-size: 40px; color: #909399"><UploadFilled /></el-icon>
            <div style="margin-top: 8px; color: #606266">拖拽 PDF 到此处，或 <em>点击选择</em></div>
            <template #tip>
              <div style="color: #9CA3AF; font-size: 12px; margin-top: 6px">
                仅支持 .pdf，建议单份试卷文件（选择题 + 判断题部分）
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <div style="margin-top: 16px; padding: 12px; background: #FEF9EC; border-radius: 8px; font-size: 13px; color: #92400E">
        <strong>提示：</strong>由 Qwen-VL 视觉模型识别题目，每页约需 5-15 秒。识别完成后可在预览中逐题确认或删除。
      </div>

      <div style="margin-top: 20px; text-align: right">
        <el-button type="primary" :loading="extracting" :disabled="!pdfFile" @click="handleExtract" style="width: 120px">
          {{ extracting ? '识别中…' : '开始识别' }}
        </el-button>
      </div>

      <!-- 进度提示 -->
      <div v-if="extracting" style="margin-top: 16px">
        <el-progress :percentage="extractProgress" :stroke-width="8" status="striped" striped-flow :duration="6" />
        <div style="text-align: center; color: #6B7280; font-size: 13px; margin-top: 6px">
          正在识别第 {{ currentPage }} / {{ totalPage }} 页…
        </div>
      </div>

      <!-- 识别失败错误提示（step 1 内，0题时显示） -->
      <el-alert v-if="extractErrors.length && !extracting" type="error" :closable="false" style="margin-top: 16px">
        <template #title>识别失败（共 {{ extractErrors.length }} 页出错）</template>
        <div v-for="e in extractErrors" :key="e" style="margin-top: 4px; font-size: 13px">{{ e }}</div>
        <div style="margin-top: 8px; font-size: 13px; color: #7F1D1D">
          若提示 401 / Incorrect API key，请前往
          <a href="https://bailian.console.aliyun.com/" target="_blank" style="color: #1865F2">阿里云百炼控制台</a>
          检查 API-KEY 是否有效，并更新 backend/.env 中的 DASHSCOPE_API_KEY。
        </div>
      </el-alert>
    </el-card>

    <!-- Step 2: 逐题确认 -->
    <div v-if="step === 2">
      <!-- 顶部工具栏 -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
        <div style="display: flex; align-items: center; gap: 10px">
          <span style="font-size: 16px; font-weight: 600">逐题核对</span>
          <el-tag type="success">共 {{ questions.length }} 题</el-tag>
          <el-tag v-if="extractErrors.length" type="warning">{{ extractErrors.length }} 页识别失败</el-tag>
          <el-progress
            :percentage="Math.round((currentIdx + 1) / questions.length * 100)"
            :stroke-width="10"
            style="width: 180px"
            :format="() => `${currentIdx + 1} / ${questions.length}`"
          />
        </div>
        <div style="display: flex; gap: 8px">
          <el-button @click="step = 1; questions = []">重新上传</el-button>
          <el-button type="primary" :loading="importing" :disabled="questions.length === 0" @click="handleImport">
            全部导入（{{ questions.length }} 题）
          </el-button>
        </div>
      </div>

      <el-alert v-if="extractErrors.length" type="warning" :closable="true" style="margin-bottom: 12px">
        <div v-for="e in extractErrors" :key="e">{{ e }}</div>
      </el-alert>

      <el-empty v-if="questions.length === 0" description="没有识别到题目，请重新上传" />

      <!-- 左右分栏：预览 + 编辑 -->
      <div v-if="questions.length > 0 && currentQ" style="display: flex; gap: 16px; align-items: flex-start">

        <!-- 左：渲染预览 -->
        <el-card style="flex: 1; min-width: 0; overflow: hidden">
          <template #header>
            <span style="font-weight: 600; color: #6B7280">预览（渲染效果）</span>
          </template>
          <div class="preview-box">
            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px">
              <el-tag size="small">{{ ['','单选题','多选题','判断题'][currentQ.question_type] }}</el-tag>
              <el-tag size="small" :type="currentQ.difficulty === 1 ? 'success' : currentQ.difficulty === 2 ? 'warning' : 'danger'">
                {{ ['','简单','中等','困难'][currentQ.difficulty] }}
              </el-tag>
              <el-tag size="small" type="info">{{ currentQ.level }}级</el-tag>
              <el-tag size="small" type="success">答案：{{ currentQ.answer }}</el-tag>
            </div>
            <div class="preview-content" v-html="renderContent(currentQ.content)" v-highlight />
            <div class="preview-options" v-if="currentQ.question_type !== 3">
              <div
                v-for="opt in (currentQ.options || [])" :key="opt.key"
                class="preview-option"
                :class="{ correct: currentQ.answer?.includes(opt.key) }"
              >
                <span class="opt-key">{{ opt.key }}</span>
                <span v-html="renderContent(opt.text)" />
              </div>
            </div>
            <div class="preview-options" v-else>
              <div class="preview-option" :class="{ correct: currentQ.answer === 'T' }">
                <span class="opt-key">T</span> 正确
              </div>
              <div class="preview-option" :class="{ correct: currentQ.answer === 'F' }">
                <span class="opt-key">F</span> 错误
              </div>
            </div>
            <div v-if="currentQ.explanation" style="margin-top: 10px; padding: 8px; background: #F0FDF4; border-radius: 6px; font-size: 13px; color: #15803D">
              <strong>解析：</strong>{{ currentQ.explanation }}
            </div>
          </div>
        </el-card>

        <!-- 右：编辑表单 -->
        <el-card style="flex: 1; min-width: 0; overflow: hidden">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600; color: #6B7280">编辑（第 {{ currentIdx + 1 }} 题）</span>
              <el-button type="danger" size="small" text @click="deleteCurrentQ">
                <el-icon><Delete /></el-icon> 删除此题
              </el-button>
            </div>
          </template>

          <el-form label-width="60px" size="small">
            <el-row :gutter="8">
              <el-col :span="8">
                <el-form-item label="题型">
                  <el-select v-model="currentQ.question_type" style="width: 100%">
                    <el-option label="单选题" :value="1" />
                    <el-option label="判断题" :value="3" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="难度">
                  <el-select v-model="currentQ.difficulty" style="width: 100%">
                    <el-option label="简单" :value="1" />
                    <el-option label="中等" :value="2" />
                    <el-option label="困难" :value="3" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="级别">
                  <el-select v-model="currentQ.level" style="width: 100%">
                    <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="题目">
              <el-input v-model="currentQ.content" type="textarea" :rows="5" style="font-family: monospace"
                placeholder="支持HTML格式，如 <pre>代码</pre>" />
            </el-form-item>

            <el-form-item v-if="currentQ.question_type !== 3" label="选项">
              <div style="width: 100%">
                <div v-for="(opt, oi) in currentQ.options" :key="oi"
                  style="display: flex; align-items: flex-start; gap: 6px; margin-bottom: 6px">
                  <span style="font-weight:600; color:#1865F2; min-width:18px; padding-top:5px">{{ opt.key }}.</span>
                  <el-input v-model="opt.text" type="textarea" :rows="2" style="font-family: monospace; flex:1"
                    :placeholder="`选项${opt.key}，支持HTML如 <pre>代码</pre>`" />
                  <el-button
                    v-if="currentQ.options.length > 2"
                    link type="danger" size="small"
                    style="padding-top: 5px; flex-shrink:0"
                    @click="removeOption(oi)"
                  ><el-icon><Delete /></el-icon></el-button>
                </div>
                <el-button
                  v-if="currentQ.options.length < 6"
                  size="small" @click="addOption"
                  style="margin-top: 2px"
                >
                  <el-icon><Plus /></el-icon> 添加选项
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="答案">
              <el-input v-model="currentQ.answer" placeholder="单选填字母如B，判断填T或F" style="width: 120px" />
            </el-form-item>

            <el-form-item label="解析">
              <el-input v-model="currentQ.explanation" type="textarea" :rows="2" placeholder="可选" />
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- 底部导航 -->
      <div v-if="questions.length > 0" style="display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 20px">
        <el-button :disabled="currentIdx === 0" @click="currentIdx--">
          <el-icon><ArrowLeft /></el-icon> 上一题
        </el-button>
        <span style="color: #6B7280; font-size: 14px">{{ currentIdx + 1 }} / {{ questions.length }}</span>
        <el-button :disabled="currentIdx === questions.length - 1" type="primary" @click="currentIdx++">
          下一题 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Step 3: 导入结果 -->
    <el-card v-if="step === 3" style="max-width: 640px; margin: 0 auto">
      <el-result
        :icon="importResult.error_count === 0 ? 'success' : 'warning'"
        :title="`成功导入 ${importResult.created_count} 道题目`"
      >
        <template #sub-title>
          <span v-if="importResult.error_count === 0">所有题目已成功写入题库</span>
          <span v-else style="color: #D97706">{{ importResult.error_count }} 题导入失败，详情如下</span>
        </template>
        <template #extra>
          <el-button type="primary" @click="$router.push('/admin/questions')">查看题库</el-button>
          <el-button @click="resetAll">继续导入</el-button>
        </template>
      </el-result>

      <!-- 失败详情 -->
      <div v-if="importResult.errors && importResult.errors.length" style="margin-top: 8px; text-align: left">
        <el-divider>失败详情</el-divider>
        <div v-for="e in importResult.errors" :key="e.index"
          style="margin-bottom: 10px; padding: 10px; background: #FEF2F2; border-radius: 6px; font-size: 13px">
          <div style="font-weight: 600; margin-bottom: 4px; color: #991B1B">
            第 {{ e.index + 1 }} 题（识别列表中第 {{ e.index + 1 }} 条）
          </div>
          <div style="color: #7F1D1D">
            <div v-for="(msgs, field) in e.errors" :key="field">
              <strong>{{ field }}：</strong>{{ Array.isArray(msgs) ? msgs.join('；') : msgs }}
            </div>
          </div>
          <div style="margin-top: 6px; color: #6B7280; font-size: 12px">
            题目内容：{{ (failedContents[e.index] || '').slice(0, 60) }}{{ failedContents[e.index]?.length > 60 ? '…' : '' }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Delete, ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { pdfExtract, pdfImportConfirm } from '../../api/admin'

const step = ref(1)
const level = ref(1)
const source = ref('')
const pdfFile = ref(null)
const uploadRef = ref(null)

const extracting = ref(false)
const extractProgress = ref(0)
const currentPage = ref(0)
const totalPage = ref(0)
const extractErrors = ref([])

const questions = ref([])
const currentIdx = ref(0)
const currentQ = computed(() => questions.value[currentIdx.value] ?? null)
const importing = ref(false)
const importResult = ref(null)
const failedContents = ref({})

function renderContent(text) {
  if (!text) return ''
  // 把 ```code``` 转为 <pre><code>，行内 `code` 转为 <code>
  return text
    .replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`)
    .replace(/`([^`]+)`/g, (_, c) => `<code>${c.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code>`)
}

function deleteCurrentQ() {
  questions.value.splice(currentIdx.value, 1)
  if (currentIdx.value >= questions.value.length) currentIdx.value = Math.max(0, questions.value.length - 1)
}

const OPTION_KEYS = ['A', 'B', 'C', 'D', 'E', 'F']

function addOption() {
  if (!currentQ.value) return
  const used = new Set(currentQ.value.options.map(o => o.key))
  const next = OPTION_KEYS.find(k => !used.has(k))
  if (next) currentQ.value.options.push({ key: next, text: '' })
}

function removeOption(idx) {
  if (!currentQ.value) return
  currentQ.value.options.splice(idx, 1)
  // 重新按 ABCDEF 顺序重排 key
  currentQ.value.options.forEach((o, i) => { o.key = OPTION_KEYS[i] })
}

function handleFileChange(file) {
  pdfFile.value = file.raw
}

async function handleExtract() {
  if (!pdfFile.value) return
  extracting.value = true
  extractProgress.value = 10
  extractErrors.value = []

  // 模拟进度（真实进度无法从 HTTP 流获取）
  const timer = setInterval(() => {
    if (extractProgress.value < 85) extractProgress.value += 5
  }, 3000)

  try {
    const formData = new FormData()
    formData.append('file', pdfFile.value)
    formData.append('level', level.value)
    formData.append('source', source.value || `GESP${level.value}级试卷`)

    const res = await pdfExtract(formData)
    totalPage.value = res.page_count || 0
    extractErrors.value = res.errors || []
    questions.value = res.questions || []

    extractProgress.value = 100
    if (questions.value.length === 0) {
      if (extractErrors.value.length > 0) {
        ElMessage.error('识别失败，请查看下方错误详情')
      } else {
        ElMessage.warning('未识别到题目，请检查PDF内容或尝试其他文件')
      }
    } else {
      ElMessage.success(`识别完成，共 ${questions.value.length} 题，请逐题核对后导入`)
      currentIdx.value = 0
      step.value = 2
    }
  } catch (e) {
    const detail = e.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
      extractErrors.value = [detail]
    } else if (e.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，PDF页数过多或网络较慢，请尝试缩短PDF或重试')
      extractErrors.value = ['请求超时（超过15分钟），建议拆分PDF后重试']
    } else {
      ElMessage.error('网络错误，请确认后端服务正在运行')
      extractErrors.value = [String(e.message || '未知网络错误')]
    }
  } finally {
    clearInterval(timer)
    extracting.value = false
  }
}

async function handleImport() {
  if (questions.value.length === 0) return
  importing.value = true
  // 保存快照，供失败详情显示题目内容
  const snapshot = questions.value.map(q => q.content || '')
  try {
    const res = await pdfImportConfirm(questions.value)
    importResult.value = res
    // 建立 index → content 映射
    failedContents.value = {}
    if (res.errors) {
      res.errors.forEach(e => { failedContents.value[e.index] = snapshot[e.index] })
    }
    step.value = 3
    if (res.error_count > 0) {
      ElMessage.warning(`导入完成：${res.created_count} 题成功，${res.error_count} 题失败`)
    } else {
      ElMessage.success(`全部 ${res.created_count} 题导入成功`)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

function resetAll() {
  step.value = 1
  pdfFile.value = null
  questions.value = []
  currentIdx.value = 0
  extractProgress.value = 0
  importResult.value = null
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.preview-box { font-size: 14px; line-height: 1.7; }
.preview-content { margin-bottom: 12px; }
.preview-content :deep(pre) {
  background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;
  padding: 10px 14px; overflow-x: auto; font-size: 13px;
}
.preview-content :deep(code) { font-family: 'Fira Code', monospace; font-size: 13px; }
.preview-options { display: flex; flex-direction: column; gap: 6px; }
.preview-option {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 6px 10px; border-radius: 6px;
  background: #F9FAFB; border: 1px solid #E5E7EB;
}
.preview-option.correct {
  background: #F0FDF4; border-color: #86EFAC; color: #15803D; font-weight: 500;
}
.opt-key {
  font-weight: 700; color: #1865F2; min-width: 18px; flex-shrink: 0;
}
.preview-option.correct .opt-key { color: #15803D; }
</style>
