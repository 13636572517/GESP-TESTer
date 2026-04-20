<template>
  <div class="prog-layout">
    <!-- 左侧题目 -->
    <div class="prog-left">
      <div class="prog-header">
        <el-button link @click="$router.back()">← 返回</el-button>
        <el-tag :type="diffType(question?.difficulty)" size="small">{{ question?.difficulty_display }}</el-tag>
        <span style="font-size:13px;color:#6B7280">{{ question?.time_limit }}ms / {{ question?.memory_limit }}MB</span>
      </div>

      <h2 style="margin: 12px 0 8px">{{ question?.title }}</h2>

      <div v-loading="loading" class="desc-block">
        <div class="section-title">题目描述</div>
        <div v-html="renderedDesc"></div>

        <template v-if="question?.input_description">
          <div class="section-title">输入说明</div>
          <div v-html="renderedInput"></div>
        </template>

        <template v-if="question?.output_description">
          <div class="section-title">输出说明</div>
          <div v-html="renderedOutput"></div>
        </template>

        <template v-if="question?.samples?.length">
          <div class="section-title">样例</div>
          <div v-for="(s, i) in question.samples" :key="i" class="sample-block">
            <div class="sample-row">
              <div class="sample-label">输入</div>
              <pre class="sample-pre">{{ s.input || '(空)' }}</pre>
            </div>
            <div class="sample-row">
              <div class="sample-label">输出</div>
              <pre class="sample-pre">{{ s.output }}</pre>
            </div>
          </div>
        </template>
      </div>

      <!-- 提交历史 -->
      <div v-if="submissions.length" style="margin-top: 16px">
        <div class="section-title">我的提交</div>
        <el-table :data="submissions" size="small">
          <el-table-column label="状态">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ row.status_display }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="通过" width="80">
            <template #default="{ row }">{{ row.passed_cases }}/{{ row.total_cases }}</template>
          </el-table-column>
          <el-table-column label="时间" width="80">
            <template #default="{ row }">{{ row.time_used ? (row.time_used * 1000).toFixed(0) + 'ms' : '-' }}</template>
          </el-table-column>
          <el-table-column label="提交时间" prop="created_at" width="130" />
        </el-table>
      </div>
    </div>

    <!-- 右侧编辑器 -->
    <div class="prog-right">
      <div class="editor-toolbar">
        <el-select v-model="language" size="small" style="width: 180px">
          <el-option label="C++ (GCC 9.2.0)" :value="54" />
        </el-select>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
      </div>

      <div ref="editorContainer" class="editor-container"></div>

      <!-- 提交结果 -->
      <div v-if="result" class="result-panel">
        <el-tag :type="statusType(result.status)" size="large">{{ result.status_display }}</el-tag>
        <span style="margin-left:12px;font-size:13px;color:#6B7280">
          {{ result.passed_cases }}/{{ result.total_cases }} 测试点通过
          <template v-if="result.time_used"> · {{ (result.time_used * 1000).toFixed(0) }}ms</template>
          <template v-if="result.memory_used"> · {{ (result.memory_used / 1024).toFixed(1) }}MB</template>
        </span>
        <pre v-if="result.compile_output" class="result-msg">{{ result.compile_output }}</pre>
        <pre v-if="result.stderr" class="result-msg">{{ result.stderr }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as monaco from 'monaco-editor'
import request from '../../utils/request'

const route = useRoute()
const loading = ref(false)
const submitting = ref(false)
const question = ref(null)
const submissions = ref([])
const result = ref(null)
const language = ref(54)
const editorContainer = ref(null)
let editor = null

function diffType(d) { return { 1: 'success', 2: 'warning', 3: 'danger' }[d] ?? '' }
function statusType(s) {
  return { 3: 'success', 4: 'danger', 5: 'warning', 6: 'warning', 7: 'danger', 8: 'danger', 13: 'info' }[s] ?? 'info'
}

const renderedDesc = computed(() => question.value?.description?.replace(/\n/g, '<br>') ?? '')
const renderedInput = computed(() => question.value?.input_description?.replace(/\n/g, '<br>') ?? '')
const renderedOutput = computed(() => question.value?.output_description?.replace(/\n/g, '<br>') ?? '')

async function loadQuestion() {
  loading.value = true
  try {
    const [qRes, sRes] = await Promise.all([
      request.get(`/programming/questions/${route.params.id}/`),
      request.get(`/programming/questions/${route.params.id}/submissions/`),
    ])
    question.value = qRes.data
    submissions.value = sRes.data
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const code = editor?.getValue() ?? ''
  if (!code.trim()) return
  submitting.value = true
  result.value = null
  try {
    const res = await request.post(`/programming/questions/${route.params.id}/submit/`, {
      code, language_id: language.value,
    })
    result.value = res.data
    const sRes = await request.get(`/programming/questions/${route.params.id}/submissions/`)
    submissions.value = sRes.data
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadQuestion()
  editor = monaco.editor.create(editorContainer.value, {
    value: '#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}',
    language: 'cpp',
    theme: 'vs',
    fontSize: 14,
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
  })
})

onUnmounted(() => editor?.dispose())
</script>

<style scoped>
.prog-layout {
  display: flex;
  height: calc(100vh - 60px);
  gap: 0;
  overflow: hidden;
}
.prog-left {
  width: 45%;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
  border-right: 1px solid #E5E7EB;
}
.prog-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.prog-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.desc-block {
  font-size: 14px;
  line-height: 1.7;
  color: #374151;
}
.section-title {
  font-weight: 600;
  font-size: 15px;
  margin: 16px 0 8px;
  color: #1865F2;
}
.sample-block {
  background: #F7F8FA;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}
.sample-row { display: flex; gap: 12px; margin-bottom: 6px; }
.sample-label { font-weight: 600; min-width: 32px; }
.sample-pre { margin: 0; font-family: monospace; white-space: pre-wrap; }
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid #E5E7EB;
}
.editor-container { flex: 1; }
.result-panel {
  padding: 12px 16px;
  border-top: 1px solid #E5E7EB;
  background: #F7F8FA;
}
.result-msg {
  margin: 8px 0 0;
  font-size: 12px;
  color: #EF4444;
  white-space: pre-wrap;
  max-height: 120px;
  overflow-y: auto;
}
</style>
