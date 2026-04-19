<template>
  <span>
    <el-tooltip content="题目反馈" placement="top">
      <el-button
        :icon="Flag"
        size="small"
        circle
        style="color:#9CA3AF;border:none;background:transparent"
        @click="open"
      />
    </el-tooltip>

    <el-dialog v-model="visible" title="题目反馈" width="420px" :close-on-click-modal="false">
      <el-form :model="form" label-width="90px">
        <el-form-item label="反馈类型" required>
          <el-radio-group v-model="form.feedback_type">
            <el-radio :value="1" style="margin-bottom:6px">答案有误</el-radio>
            <el-radio :value="2" style="margin-bottom:6px">题目表述不清</el-radio>
            <el-radio :value="3" style="margin-bottom:6px">选项有问题</el-radio>
            <el-radio :value="4">其他</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="补充描述">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="3"
            placeholder="请描述具体问题（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交反馈</el-button>
      </template>
    </el-dialog>
  </span>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Flag } from '@element-plus/icons-vue'
import { submitQuestionFeedback } from '../api/feedback'

const props = defineProps({ questionId: { type: Number, required: true } })

const visible = ref(false)
const submitting = ref(false)
const form = reactive({ feedback_type: 1, content: '' })

function open() {
  form.feedback_type = 1
  form.content = ''
  visible.value = true
}

async function submit() {
  submitting.value = true
  try {
    await submitQuestionFeedback(props.questionId, {
      feedback_type: form.feedback_type,
      content: form.content,
    })
    ElMessage.success('反馈已提交，感谢您的反馈！')
    visible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>
