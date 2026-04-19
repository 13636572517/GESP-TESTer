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

    <!-- Step 2: 预览确认 -->
    <div v-if="step === 2">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
        <div>
          <span style="font-size: 16px; font-weight: 600">识别结果预览</span>
          <el-tag style="margin-left: 10px" type="success">共 {{ questions.length }} 题</el-tag>
          <el-tag v-if="extractErrors.length" type="warning" style="margin-left: 6px">{{ extractErrors.length }} 页识别失败</el-tag>
        </div>
        <div style="display: flex; gap: 8px">
          <el-button @click="step = 1; questions = []">重新上传</el-button>
          <el-button type="primary" :loading="importing" :disabled="questions.length === 0" @click="handleImport">
            确认导入 {{ questions.length }} 题
          </el-button>
        </div>
      </div>

      <!-- 识别失败提示 -->
      <el-alert v-if="extractErrors.length" type="warning" :closable="false" style="margin-bottom: 12px">
        <div v-for="e in extractErrors" :key="e">{{ e }}</div>
      </el-alert>

      <!-- 题目预览表 -->
      <el-card v-for="(q, idx) in questions" :key="idx" class="question-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px">
          <div style="flex: 1; min-width: 0">
            <!-- 题目头部 -->
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap">
              <span style="font-weight: 600; color: #6B7280; min-width: 28px">{{ idx + 1 }}.</span>
              <el-select v-model="q.question_type" size="small" style="width: 90px">
                <el-option label="单选题" :value="1" />
                <el-option label="判断题" :value="3" />
              </el-select>
              <el-select v-model="q.difficulty" size="small" style="width: 80px">
                <el-option label="简单" :value="1" />
                <el-option label="中等" :value="2" />
                <el-option label="困难" :value="3" />
              </el-select>
              <el-select v-model="q.level" size="small" style="width: 80px">
                <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
              </el-select>
              <el-tag size="small" type="info">答案：{{ q.answer }}</el-tag>
            </div>

            <!-- 题目内容 -->
            <el-input v-model="q.content" type="textarea" :rows="3" size="small"
              style="margin-bottom: 8px; font-family: monospace" />

            <!-- 选项（单选题）-->
            <div v-if="q.question_type === 1" style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px">
              <div v-for="(opt, oi) in q.options" :key="oi" style="display: flex; align-items: center; gap: 6px">
                <span style="font-weight: 600; color: #1865F2; min-width: 18px">{{ opt.key }}.</span>
                <el-input v-model="opt.text" size="small" :placeholder="`选项${opt.key}`" />
              </div>
            </div>

            <!-- 解析 -->
            <el-input v-model="q.explanation" placeholder="解析（可选）" size="small"
              style="margin-top: 8px" />
          </div>

          <!-- 删除按钮 -->
          <el-button type="danger" circle size="small" @click="questions.splice(idx, 1)"
            style="flex-shrink: 0; margin-top: 4px">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </el-card>

      <el-empty v-if="questions.length === 0" description="没有识别到题目，请重新上传" />

      <div v-if="questions.length > 0" style="text-align: right; margin-top: 16px">
        <el-button type="primary" :loading="importing" @click="handleImport">
          确认导入 {{ questions.length }} 题
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Delete } from '@element-plus/icons-vue'
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
const importing = ref(false)
const importResult = ref(null)
const failedContents = ref({}) // index → content，供失败详情显示

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
      ElMessage.success(`识别完成，共 ${questions.value.length} 题，请确认后导入`)
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
  extractProgress.value = 0
  importResult.value = null
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.question-card {
  margin-bottom: 12px;
  border-left: 3px solid #E5E7EB;
  transition: border-color 0.15s;
}
.question-card:hover {
  border-left-color: #1865F2;
}
</style>
