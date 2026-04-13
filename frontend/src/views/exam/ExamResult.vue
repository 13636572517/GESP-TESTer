<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/exam')">
      <template #content>考试结果</template>
    </el-page-header>

    <div v-if="result.record" style="margin-top: 20px">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-card>
            <div style="text-align: center">
              <div :class="['score', result.passed ? 'pass' : 'fail']">
                {{ result.record.earned_score }}
              </div>
              <div style="color: #909399; margin-top: 4px">/ {{ result.record.total_score }} 分</div>
              <el-tag :type="result.passed ? 'success' : 'danger'" style="margin-top: 12px">
                {{ result.passed ? '通过' : '未通过' }}
              </el-tag>
              <div v-if="result.passed" style="margin-top: 12px; color: #10b981; font-weight: 500">🎉 恭喜通过考试！</div>
              <div v-else style="margin-top: 12px; color: #ef4444; font-weight: 500">💪 继续努力，下次一定行！</div>
              <div style="margin-top: 16px; font-size: 14px; color: #909399">
                切屏次数: {{ result.record.switch_count }}
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="16">
          <el-card>
            <template #header>逐题分析</template>
            <div v-for="(answer, i) in result.answers" :key="answer.id" style="padding: 12px 0; border-bottom: 1px solid #f0f0ff">
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span style="font-weight: 500">第 {{ i + 1 }} 题 ({{ answer.score }}分)</span>
                <el-tag :type="answer.is_correct ? 'success' : 'danger'" size="small">
                  {{ answer.is_correct ? '正确' : '错误' }}
                </el-tag>
              </div>
              <div style="font-size: 14px; color: #606266; margin-top: 4px" v-html="answer.question?.content?.substring(0, 120)" v-highlight></div>
              <div v-if="!answer.is_correct" style="font-size: 13px; margin-top: 4px">
                <span style="color: #ef4444">你的答案: {{ answer.user_answer || '未作答' }}</span>
                <span style="color: #10b981; margin-left: 12px">正确答案: {{ answer.question?.answer }}</span>
              </div>
              <div v-if="answer.question?.explanation" style="font-size: 13px; color: #909399; margin-top: 4px">
                解析: {{ answer.question.explanation }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getExamResult } from '../../api/exam'

const route = useRoute()
const result = ref({})

onMounted(async () => {
  result.value = await getExamResult(route.params.id)
})
</script>

<style scoped>
.score {
  font-size: 56px;
  font-weight: 700;
}
.score.pass { color: #10b981; }
.score.fail { color: #ef4444; }
</style>
