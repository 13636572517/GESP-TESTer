<template>
  <div class="page-container">
    <el-page-header @back="handleBack">
      <template #content>
        <span>练习中 - 第 {{ currentIndex + 1 }}/{{ questions.length }} 题</span>
      </template>
      <template #extra>
        <el-button type="danger" @click="handleFinish">结束练习</el-button>
      </template>
    </el-page-header>

    <el-progress
      :percentage="Math.round((answeredCount / questions.length) * 100)"
      :stroke-width="8"
      style="margin: 16px 0"
    />

    <el-card v-if="currentQuestion" style="margin-top: 16px">
      <div class="question-header">
        <el-tag>{{ currentQuestion.type_display }}</el-tag>
        <span style="margin-left: 8px; color: #909399">第 {{ currentIndex + 1 }} 题</span>
      </div>

      <div class="question-content" v-html="currentQuestion.content" v-highlight></div>

      <div class="options" v-if="currentQuestion.question_type !== 3">
        <div
          v-for="opt in currentQuestion.options"
          :key="opt.key"
          :class="['option-item', optionClass(opt.key)]"
          @click="selectOption(opt.key)"
        >
          <span class="option-key">{{ opt.key }}</span>
          <span v-html="opt.text"></span>
        </div>
      </div>

      <div class="options" v-else>
        <div
          :class="['option-item', optionClass('T')]"
          @click="selectOption('T')"
        >
          <span class="option-key">T</span>
          <span>正确</span>
        </div>
        <div
          :class="['option-item', optionClass('F')]"
          @click="selectOption('F')"
        >
          <span class="option-key">F</span>
          <span>错误</span>
        </div>
      </div>

      <!-- 答题结果 -->
      <div v-if="currentResult" class="result-box" :class="currentResult.is_correct ? 'correct' : 'wrong'">
        <div style="font-weight: 600; margin-bottom: 8px">
          {{ currentResult.is_correct ? '回答正确!' : '回答错误' }}
          <span v-if="!currentResult.is_correct" style="margin-left: 8px">正确答案: {{ currentResult.correct_answer }}</span>
        </div>
        <div v-if="currentResult.explanation" style="color: #606266; font-size: 14px">
          {{ currentResult.explanation }}
        </div>
      </div>
    </el-card>

    <div style="display: flex; justify-content: space-between; margin-top: 16px">
      <el-button @click="prevQuestion" :disabled="currentIndex === 0">上一题</el-button>
      <el-button type="primary" @click="nextQuestion" :disabled="currentIndex === questions.length - 1">下一题</el-button>
    </div>

    <!-- 题目导航 -->
    <el-card style="margin-top: 16px">
      <template #header>题目导航</template>
      <div class="question-nav">
        <div
          v-for="(q, i) in questions"
          :key="q.id"
          :class="['nav-item', navItemClass(i)]"
          @click="currentIndex = i"
        >
          {{ i + 1 }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { submitAnswer, finishPractice } from '../../api/practice'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id
const questions = ref([])
const currentIndex = ref(0)
const selectedAnswers = ref({})
const results = ref({})
const startTime = ref(Date.now())

const currentQuestion = computed(() => questions.value[currentIndex.value])
const currentResult = computed(() => results.value[currentQuestion.value?.id])
const answeredCount = computed(() => Object.keys(results.value).length)

function optionClass(key) {
  const qid = currentQuestion.value?.id
  const result = results.value[qid]
  const selected = selectedAnswers.value[qid]
  if (!result) {
    return selected === key ? 'selected' : ''
  }
  if (key === result.correct_answer) return 'correct'
  if (selected === key && !result.is_correct) return 'wrong'
  return ''
}

function navItemClass(index) {
  const q = questions.value[index]
  if (index === currentIndex.value) return 'active'
  const result = results.value[q.id]
  if (result?.is_correct) return 'correct'
  if (result && !result.is_correct) return 'wrong'
  return ''
}

async function selectOption(key) {
  const qid = currentQuestion.value.id
  if (results.value[qid]) return // 已答过

  selectedAnswers.value[qid] = key
  const timeSpent = Math.round((Date.now() - startTime.value) / 1000)

  const result = await submitAnswer(sessionId, {
    question_id: qid,
    user_answer: key,
    time_spent: timeSpent,
  })
  results.value[qid] = result
  startTime.value = Date.now()
}

function prevQuestion() {
  if (currentIndex.value > 0) currentIndex.value--
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

async function handleBack() {
  await ElMessageBox.confirm('确定退出练习？', '提示')
  router.push('/practice')
}

async function handleFinish() {
  await ElMessageBox.confirm('确定结束练习？', '提示')
  await finishPractice(sessionId)
  router.push(`/practice/${sessionId}/result`)
}

onMounted(() => {
  // 从sessionStorage获取练习题目（由Practice页面传递）
  const cached = sessionStorage.getItem(`practice_${sessionId}`)
  if (cached) {
    questions.value = JSON.parse(cached)
  }
})
</script>

<style scoped>
.question-header {
  margin-bottom: 16px;
}
.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 20px;
  padding: 16px;
  background: #fafafa;
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
.option-item:hover {
  border-color: #409eff;
}
.option-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}
.option-item.correct {
  border-color: #67c23a;
  background: #f0f9eb;
}
.option-item.wrong {
  border-color: #f56c6c;
  background: #fef0f0;
}
.option-key {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}
.result-box {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
}
.result-box.correct {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}
.result-box.wrong {
  background: #fef0f0;
  border: 1px solid #fde2e2;
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
  border-color: #409eff;
  color: #409eff;
  font-weight: 600;
}
.nav-item.correct {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}
.nav-item.wrong {
  background: #f56c6c;
  color: #fff;
  border-color: #f56c6c;
}
</style>
