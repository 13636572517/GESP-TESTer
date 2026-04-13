<template>
  <div class="exam-container">
    <!-- 顶栏 -->
    <div class="exam-header">
      <span style="font-size: 18px; font-weight: 600">模拟考试</span>
      <div class="timer" :class="{ warning: remainingMinutes <= 5 }">
        <el-icon><Timer /></el-icon>
        {{ formatTime(remainingSeconds) }}
      </div>
      <div style="display: flex; gap: 12px; align-items: center">
        <el-tag v-if="switchCount > 0" type="danger" size="small">切屏 {{ switchCount }} 次</el-tag>
        <el-button type="danger" @click="handleSubmit(false)">交卷</el-button>
      </div>
    </div>

    <div class="exam-body">
      <!-- 题目区域 -->
      <div class="exam-main">
        <el-card v-if="currentQuestion">
          <div class="question-header">
            <el-tag>{{ currentQuestion.type_display }}</el-tag>
            <span style="margin-left: 8px; color: #6B7280">第 {{ currentIndex + 1 }}/{{ questions.length }} 题</span>
          </div>

          <div class="question-content" v-html="currentQuestion.content" v-highlight></div>

          <div class="options" v-if="currentQuestion.question_type !== 3">
            <div
              v-for="opt in currentQuestion.options"
              :key="opt.key"
              :class="['option-item', answers[currentQuestion.id] === opt.key ? 'selected' : '']"
              @click="selectAnswer(opt.key)"
            >
              <span class="option-key">{{ opt.key }}</span>
              <span v-html="opt.text"></span>
            </div>
          </div>

          <div class="options" v-else>
            <div
              :class="['option-item', answers[currentQuestion.id] === 'T' ? 'selected' : '']"
              @click="selectAnswer('T')"
            >
              <span class="option-key">T</span>
              <span>正确</span>
            </div>
            <div
              :class="['option-item', answers[currentQuestion.id] === 'F' ? 'selected' : '']"
              @click="selectAnswer('F')"
            >
              <span class="option-key">F</span>
              <span>错误</span>
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; margin-top: 20px">
            <el-button @click="prevQuestion" :disabled="currentIndex === 0">上一题</el-button>
            <el-button type="primary" @click="nextQuestion" :disabled="currentIndex === questions.length - 1">下一题</el-button>
          </div>
        </el-card>
      </div>

      <!-- 题目导航 -->
      <div class="exam-sidebar">
        <el-card>
          <template #header>答题卡</template>
          <div class="question-nav">
            <div
              v-for="(q, i) in questions"
              :key="q.id"
              :class="['nav-item', { active: i === currentIndex, answered: !!answers[q.id] }]"
              @click="currentIndex = i"
            >
              {{ i + 1 }}
            </div>
          </div>
          <div style="margin-top: 16px; font-size: 14px; color: #6B7280">
            已答: {{ answeredCount }} / {{ questions.length }}
          </div>
        </el-card>
      </div>
    </div>

    <!-- 切屏警告弹窗 -->
    <el-dialog v-model="showSwitchWarning" title="警告" :close-on-click-modal="false" width="400px">
      <div style="text-align: center; padding: 20px">
        <el-icon :size="48" color="#D92916"><WarningFilled /></el-icon>
        <p style="margin-top: 16px; font-size: 16px">您已切屏 {{ switchCount }} 次</p>
        <p style="color: #6B7280">考试中请勿离开页面</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showSwitchWarning = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getExam, saveExamAnswer, submitExam, reportSwitch } from '../../api/exam'

const route = useRoute()
const router = useRouter()
const recordId = route.params.id

const questions = ref([])
const currentIndex = ref(0)
const answers = ref({})
const remainingSeconds = ref(0)
const switchCount = ref(0)
const showSwitchWarning = ref(false)
let timer = null
let autoSaveTimer = null

const currentQuestion = computed(() => questions.value[currentIndex.value])
const answeredCount = computed(() => Object.keys(answers.value).filter(k => answers.value[k]).length)
const remainingMinutes = computed(() => Math.floor(remainingSeconds.value / 60))

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

async function selectAnswer(key) {
  const qid = currentQuestion.value.id
  answers.value[qid] = key

  // 实时保存到后端
  try {
    await saveExamAnswer(recordId, {
      question_id: qid,
      user_answer: key,
      time_spent: 0,
    })
  } catch { /* 静默失败，自动保存会补偿 */ }
}

function prevQuestion() {
  if (currentIndex.value > 0) currentIndex.value--
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

async function handleSubmit(auto = false) {
  if (!auto) {
    const unanswered = questions.value.length - answeredCount.value
    if (unanswered > 0) {
      await ElMessageBox.confirm(
        `还有 ${unanswered} 题未作答，确定交卷吗？`,
        '确认交卷'
      )
    } else {
      await ElMessageBox.confirm('确定交卷吗？', '确认交卷')
    }
  }

  const data = await submitExam(recordId, { auto })
  if (timer) clearInterval(timer)
  if (autoSaveTimer) clearInterval(autoSaveTimer)
  ElMessage.success(auto ? '考试时间到，已自动交卷' : '交卷成功')
  router.replace(`/exam/${recordId}/result`)
}

// 切屏检测
function handleVisibilityChange() {
  if (document.hidden) {
    switchCount.value++
    reportSwitch(recordId).catch(() => {})
    showSwitchWarning.value = true
  }
}

onMounted(async () => {
  const data = await getExam(recordId)

  if (data.status !== 0) {
    router.replace(`/exam/${recordId}/result`)
    return
  }

  questions.value = data.questions
  answers.value = data.saved_answers || {}

  // 计算剩余时间
  const startTime = new Date(data.start_time).getTime()
  const duration = data.duration * 60 * 1000
  const endTime = startTime + duration
  remainingSeconds.value = Math.max(0, Math.floor((endTime - Date.now()) / 1000))

  // 倒计时
  timer = setInterval(() => {
    remainingSeconds.value--
    if (remainingSeconds.value <= 0) {
      handleSubmit(true)
    }
  }, 1000)

  // 自动保存定时器（每30秒批量保存未保存的答案）
  autoSaveTimer = setInterval(async () => {
    for (const q of questions.value) {
      const ans = answers.value[q.id]
      if (ans) {
        try {
          await saveExamAnswer(recordId, {
            question_id: q.id,
            user_answer: ans,
            time_spent: 0,
          })
        } catch { /* 静默失败 */ }
      }
    }
  }, 30000)

  // 切屏监听
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (autoSaveTimer) clearInterval(autoSaveTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.exam-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F7F8FA;
}
.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}
.timer {
  font-size: 24px;
  font-weight: 700;
  font-family: monospace;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #21242C;
}
.timer.warning {
  color: #D92916;
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0.5; }
}
.exam-body {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
  overflow-y: auto;
}
.exam-main {
  flex: 1;
}
.exam-sidebar {
  width: 280px;
  flex-shrink: 0;
}
.question-header { margin-bottom: 16px; }
.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 20px;
  padding: 16px;
  background: #F7F8FA;
  border-radius: 8px;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.option-item:hover { border-color: #1865F2; }
.option-item.selected {
  border-color: #1865F2;
  background: #eef2ff;
}
.option-key {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #EBF0FF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}
.question-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.nav-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.nav-item.active {
  border-color: #1865F2;
  color: #1865F2;
  font-weight: 600;
}
.nav-item.answered {
  background: #1865F2;
  color: #fff;
  border-color: #1865F2;
}
</style>
