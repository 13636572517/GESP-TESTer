<template>
  <div class="page-container">
    <h1 class="page-title">题目反馈</h1>

    <!-- 筛选 -->
    <el-card style="margin-bottom:16px">
      <el-radio-group v-model="statusFilter" @change="loadFeedbacks">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button :value="0">待处理</el-radio-button>
        <el-radio-button :value="1">已处理</el-radio-button>
        <el-radio-button :value="2">已忽略</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 列表 -->
    <el-card>
      <el-table :data="feedbacks" stripe v-loading="loading">
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="反馈类型" prop="feedback_type_display" width="120" />
        <el-table-column label="题目内容" min-width="200">
          <template #default="{ row }">
            <span style="color:#606266;font-size:13px" v-html="row.question_content" />
          </template>
        </el-table-column>
        <el-table-column label="反馈描述" prop="content" min-width="160" show-overflow-tooltip />
        <el-table-column label="学员" width="120">
          <template #default="{ row }">
            {{ row.user_nickname }}<br>
            <span style="color:#9CA3AF;font-size:12px">{{ row.user_phone }}</span>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" prop="created_at" width="140" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">处理</el-button>
            <el-divider direction="vertical" />
            <el-button link type="primary" size="small" @click="openEditQuestion(row)">修正题目</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px;display:flex;justify-content:flex-end"
        @current-change="loadFeedbacks"
      />
    </el-card>

    <!-- 处理反馈弹窗 -->
    <el-dialog v-model="detailVisible" title="处理反馈" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="反馈类型">{{ currentFeedback?.feedback_type_display }}</el-descriptions-item>
        <el-descriptions-item label="反馈内容">{{ currentFeedback?.content || '（无）' }}</el-descriptions-item>
        <el-descriptions-item label="题目">
          <span v-html="currentFeedback?.question_content" />
        </el-descriptions-item>
        <el-descriptions-item label="学员">{{ currentFeedback?.user_nickname }}</el-descriptions-item>
      </el-descriptions>

      <el-form style="margin-top:16px" label-width="90px">
        <el-form-item label="处理结果">
          <el-radio-group v-model="handleForm.status">
            <el-radio :value="1">已处理</el-radio>
            <el-radio :value="2">已忽略</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="管理员回复">
          <el-input v-model="handleForm.admin_reply" type="textarea" :rows="3" placeholder="可选，学员将看到此回复" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" :loading="handling" @click="submitHandle">确认处理</el-button>
      </template>
    </el-dialog>

    <!-- 修正题目弹窗 -->
    <el-dialog v-model="editQuestionVisible" title="修正题目" width="700px" :close-on-click-modal="false">
      <el-form :model="questionForm" label-width="90px" v-if="questionForm">
        <el-form-item label="题目内容">
          <el-input v-model="questionForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="答案">
          <el-input v-model="questionForm.answer" style="width:120px" />
          <span style="margin-left:8px;color:#9CA3AF;font-size:12px">选择题填A/B/C/D，判断题填T/F</span>
        </el-form-item>
        <el-form-item label="解析">
          <el-input v-model="questionForm.explanation" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="选项" v-if="questionForm.question_type !== 3">
          <div v-for="opt in questionForm.options" :key="opt.key" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
            <span style="width:20px;font-weight:600">{{ opt.key }}.</span>
            <el-input v-model="opt.text" style="flex:1" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editQuestionVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingQuestion" @click="saveQuestion">保存修正</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminFeedbacks, handleAdminFeedback } from '../../api/feedback'
import { getAdminQuestionDetail, updateAdminQuestion } from '../../api/admin'

const feedbacks = ref([])
const loading = ref(false)
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)

async function loadFeedbacks() {
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize }
    if (statusFilter.value !== '') params.status = statusFilter.value
    const res = await getAdminFeedbacks(params)
    feedbacks.value = res.results
    total.value = res.count
  } finally {
    loading.value = false
  }
}

function statusTagType(s) {
  return s === 0 ? 'danger' : s === 1 ? 'success' : 'info'
}

// ─── 处理反馈 ────────────────────────────────────────
const detailVisible = ref(false)
const currentFeedback = ref(null)
const handling = ref(false)
const handleForm = reactive({ status: 1, admin_reply: '' })

function openDetail(row) {
  currentFeedback.value = row
  handleForm.status = row.status === 0 ? 1 : row.status
  handleForm.admin_reply = row.admin_reply || ''
  detailVisible.value = true
}

async function submitHandle() {
  handling.value = true
  try {
    await handleAdminFeedback(currentFeedback.value.id, {
      status: handleForm.status,
      admin_reply: handleForm.admin_reply,
    })
    ElMessage.success('处理成功')
    detailVisible.value = false
    loadFeedbacks()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    handling.value = false
  }
}

// ─── 修正题目 ────────────────────────────────────────
const editQuestionVisible = ref(false)
const questionForm = ref(null)
const savingQuestion = ref(false)
const editingQuestionId = ref(null)

async function openEditQuestion(row) {
  try {
    const q = await getAdminQuestionDetail(row.question_id)
    editingQuestionId.value = row.question_id
    questionForm.value = {
      content: q.content,
      answer: q.answer,
      explanation: q.explanation,
      options: q.options ? JSON.parse(JSON.stringify(q.options)) : [],
      question_type: q.question_type,
    }
    editQuestionVisible.value = true
  } catch {
    ElMessage.error('获取题目失败')
  }
}

async function saveQuestion() {
  savingQuestion.value = true
  try {
    await updateAdminQuestion(editingQuestionId.value, {
      content: questionForm.value.content,
      answer: questionForm.value.answer,
      explanation: questionForm.value.explanation,
      options: questionForm.value.options,
    })
    ElMessage.success('题目已修正')
    editQuestionVisible.value = false
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingQuestion.value = false
  }
}

onMounted(loadFeedbacks)
</script>
