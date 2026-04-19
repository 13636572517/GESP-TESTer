<template>
  <div class="page-container">
    <h1 class="page-title">我的反馈</h1>

    <el-card v-loading="loading">
      <el-empty v-if="!loading && feedbacks.length === 0" description="暂无反馈记录" />

      <el-timeline v-else>
        <el-timeline-item
          v-for="fb in feedbacks"
          :key="fb.id"
          :timestamp="fb.created_at"
          placement="top"
          :type="statusType(fb.status)"
        >
          <el-card shadow="never" class="fb-card">
            <div class="fb-header">
              <el-tag size="small" :type="typeTagType(fb.feedback_type)">{{ fb.feedback_type_display }}</el-tag>
              <el-tag size="small" :type="statusType(fb.status)" style="margin-left: 8px">{{ fb.status_display }}</el-tag>
            </div>

            <div class="fb-question">{{ fb.question_content }}</div>

            <div v-if="fb.content" class="fb-content">
              <span class="label">描述：</span>{{ fb.content }}
            </div>

            <div v-if="fb.admin_reply" class="fb-reply">
              <span class="label">管理员回复：</span>{{ fb.admin_reply }}
              <span v-if="fb.handled_at" class="reply-time">（{{ fb.handled_at }}）</span>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../../utils/request'

const loading = ref(false)
const feedbacks = ref([])

function statusType(status) {
  return { 0: 'warning', 1: 'success', 2: 'info' }[status] ?? ''
}

function typeTagType(type) {
  return { 1: 'danger', 2: 'warning', 3: 'warning', 4: '' }[type] ?? ''
}

async function load() {
  loading.value = true
  try {
    const res = await request.get('/questions/my-feedbacks/')
    feedbacks.value = res.data.results
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.fb-card {
  background: #F7F8FA;
}
.fb-header {
  margin-bottom: 8px;
}
.fb-question {
  font-size: 14px;
  color: #374151;
  margin-bottom: 6px;
  line-height: 1.5;
}
.fb-content, .fb-reply {
  font-size: 13px;
  color: #6B7280;
  margin-top: 4px;
}
.fb-reply {
  color: #1865F2;
}
.label {
  font-weight: 600;
}
.reply-time {
  font-size: 12px;
  color: #9CA3AF;
}
</style>
