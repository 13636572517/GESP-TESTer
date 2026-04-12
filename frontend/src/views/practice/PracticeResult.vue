<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/practice')">
      <template #content>练习结果</template>
    </el-page-header>

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="8">
        <el-card>
          <div style="text-align: center">
            <div class="stat-value" style="font-size: 48px">{{ result.accuracy }}%</div>
            <div class="stat-label">正确率</div>
            <div style="margin-top: 12px; color: #606266">
              {{ result.correct_count }} / {{ result.total_count }} 题
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>答题详情</template>
          <div v-for="(answer, i) in result.answers || []" :key="answer.id" style="padding: 12px 0; border-bottom: 1px solid #f0f0f0">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>第 {{ i + 1 }} 题</span>
              <el-tag :type="answer.is_correct ? 'success' : 'danger'" size="small">
                {{ answer.is_correct ? '正确' : '错误' }}
              </el-tag>
            </div>
            <div style="font-size: 14px; color: #606266; margin-top: 4px" v-html="answer.question?.content?.substring(0, 100)" v-highlight></div>
            <div v-if="!answer.is_correct" style="font-size: 13px; color: #f56c6c; margin-top: 4px">
              你的答案: {{ answer.user_answer }} | 正确答案: {{ answer.question?.answer }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div style="text-align: center; margin-top: 20px">
      <el-button type="primary" @click="$router.push('/practice')">继续练习</el-button>
      <el-button @click="$router.push('/mistakes')">查看错题本</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { finishPractice } from '../../api/practice'

const route = useRoute()
const result = ref({})

onMounted(async () => {
  try {
    result.value = await finishPractice(route.params.id)
  } catch {
    // 可能已经结束过了
  }
})
</script>
