<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/exam')">
      <template #content>考试结果</template>
    </el-page-header>

    <div v-if="result.record" style="margin-top: 20px">
      <el-row :gutter="16">
        <!-- 得分卡 -->
        <el-col :span="8">
          <el-card>
            <div style="text-align: center">
              <div :class="['score', result.passed ? 'pass' : 'fail']">
                {{ result.record.earned_score }}
              </div>
              <div style="color: #6B7280; margin-top: 4px">/ {{ result.record.total_score }} 分</div>
              <el-tag :type="result.passed ? 'success' : 'danger'" style="margin-top: 12px">
                {{ result.passed ? '通过' : '未通过' }}
              </el-tag>
              <div v-if="result.passed" style="margin-top: 12px; color: #00A60E; font-weight: 500">恭喜通过考试！</div>
              <div v-else style="margin-top: 12px; color: #D92916; font-weight: 500">继续努力，下次一定行！</div>
              <div style="margin-top: 16px; font-size: 14px; color: #6B7280">
                切屏次数: {{ result.record.switch_count }}
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 逐题分析 -->
        <el-col :span="16">
          <el-card>
            <template #header>逐题分析</template>
            <div v-for="(answer, i) in result.answers" :key="answer.id" class="question-row">
              <div class="question-header">
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-weight:500">第 {{ i + 1 }} 题</span>
                  <el-tag size="small" type="info">{{ answer.score }}分</el-tag>
                  <el-tag :type="answer.is_correct ? 'success' : 'danger'" size="small">
                    {{ answer.is_correct ? '✓ 正确' : '✗ 错误' }}
                  </el-tag>
                </div>
                <button class="btn-ai" @click="aiDialog.open({
                  question:   answer.question,
                  userAnswer: answer.user_answer,
                  isCorrect:  answer.is_correct,
                  title:      `第 ${i + 1} 题 · AI 讲解`,
                })">
                  💬 AI 讲解
                </button>
              </div>
              <div class="question-content" v-html="answer.question?.content?.substring(0, 150)" v-highlight></div>
              <div v-if="!answer.is_correct" class="answer-row">
                <span class="wrong-ans">你的答案：{{ answer.user_answer || '未作答' }}</span>
                <span class="right-ans">正确答案：{{ answer.question?.answer }}</span>
              </div>
              <div v-if="answer.question?.explanation" class="explanation">
                解析：{{ answer.question.explanation }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <AIExplainDialog ref="aiDialog" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getExamResult } from '../../api/exam'
import AIExplainDialog from '../../components/AIExplainDialog.vue'

const route    = useRoute()
const result   = ref({})
const aiDialog = ref(null)

onMounted(async () => {
  result.value = await getExamResult(route.params.id)
})
</script>

<style scoped>
.score { font-size: 56px; font-weight: 700; }
.score.pass { color: #00A60E; }
.score.fail { color: #D92916; }

.question-row {
  padding: 14px 0;
  border-bottom: 1px solid #E5E7EB;
}
.question-row:last-child { border-bottom: none; }

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.question-content {
  font-size: 14px;
  color: #374151;
  margin-bottom: 4px;
  line-height: 1.6;
}

.answer-row {
  font-size: 13px;
  margin-top: 4px;
  display: flex;
  gap: 16px;
}
.wrong-ans { color: #D92916; }
.right-ans  { color: #00A60E; }

.explanation {
  font-size: 13px;
  color: #6B7280;
  margin-top: 4px;
  padding: 6px 8px;
  background: #F9FAFB;
  border-radius: 4px;
}

/* AI 讲解按钮 */
.btn-ai {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  height: 28px;
  font-size: 12px;
  font-weight: 500;
  color: #1865F2;
  background: #EBF0FF;
  border: 1px solid #B8D1FB;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn-ai:hover {
  color: #fff;
  background: #1865F2;
  border-color: #1865F2;
}
</style>
