<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/teacher/classes')">
      <template #content>{{ classroom.name || '班级学情' }}</template>
    </el-page-header>

    <div style="margin-top: 16px; display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
      <span style="font-size: 13px; color: #6B7280">时间范围：</span>
      <el-radio-group v-model="days" size="small" @change="loadData">
        <el-radio-button value="7">近7天</el-radio-button>
        <el-radio-button value="30">近30天</el-radio-button>
        <el-radio-button value="all">全部</el-radio-button>
      </el-radio-group>
      <span v-if="classroom.level_name" style="margin-left: auto">
        <el-tag type="info">{{ classroom.level_name }}</el-tag>
      </span>
    </div>

    <el-card v-loading="loading">
      <el-table :data="students" stripe>
        <el-table-column prop="nickname" label="姓名" width="110" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="级别" width="70">
          <template #default="{ row }">
            <el-tag size="small">{{ row.current_level }}级</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="study_days" label="学习天数" width="90" />
        <el-table-column prop="practice_count" label="练习题数" width="90" />
        <el-table-column label="正确率" width="90">
          <template #default="{ row }">
            <span v-if="row.practice_count > 0">
              {{ Math.round(row.correct_count / row.practice_count * 100) }}%
            </span>
            <span v-else style="color:#9CA3AF">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="exam_count" label="模考次数" width="90" />
        <el-table-column label="平均分" width="90">
          <template #default="{ row }">
            <span v-if="row.exam_count > 0" :class="row.avg_score >= 60 ? 'score-pass' : 'score-fail'">
              {{ row.avg_score }}
            </span>
            <span v-else style="color:#9CA3AF">—</span>
          </template>
        </el-table-column>
        <el-table-column label="最近学习" width="110">
          <template #default="{ row }">
            <span v-if="row.last_active" style="font-size: 12px; color: #6B7280">{{ row.last_active }}</span>
            <span v-else style="color:#9CA3AF">未学习</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn" size="small" @click="openExamDetail(row)">模考记录</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && students.length === 0" description="班级暂无学员" />
    </el-card>

    <!-- 模考记录下钻弹窗 -->
    <el-dialog
      v-model="examDialogVisible"
      :title="`${selectedStudent?.nickname} · 模考记录`"
      width="680px"
      align-center
    >
      <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px">
        <span style="font-size: 13px; color: #6B7280">时间范围：</span>
        <el-radio-group v-model="examDays" size="small" @change="loadExams">
          <el-radio-button value="7">近7天</el-radio-button>
          <el-radio-button value="30">近30天</el-radio-button>
          <el-radio-button value="all">全部</el-radio-button>
        </el-radio-group>
      </div>
      <el-table :data="examRecords" stripe size="small" v-loading="examsLoading">
        <el-table-column prop="exam_name" label="试卷名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="level_name" label="级别" width="70" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.exam_type === 1 ? '' : 'success'">
              {{ row.exam_type === 1 ? '真题' : '随机卷' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="得分" width="100">
          <template #default="{ row }">
            <span :class="row.passed ? 'score-pass' : 'score-fail'">
              {{ row.earned_score }} / {{ row.total_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
              {{ row.passed ? '通过' : '未通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="110">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #6B7280">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!examsLoading && examRecords.length === 0" description="该时间段内暂无模考记录" :image-size="60" />
      <template #footer>
        <el-button @click="examDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTeacherClassOverview, getTeacherStudentExams } from '../../api/admin'

const route = useRoute()
const classId = route.params.id

const loading = ref(false)
const days = ref('30')
const classroom = ref({})
const students = ref([])

const examDialogVisible = ref(false)
const examsLoading = ref(false)
const examDays = ref('30')
const examRecords = ref([])
const selectedStudent = ref(null)

async function loadData() {
  loading.value = true
  try {
    const res = await getTeacherClassOverview(classId, { days: days.value })
    classroom.value = res.classroom
    students.value = res.students
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function openExamDetail(student) {
  selectedStudent.value = student
  examDays.value = days.value
  examDialogVisible.value = true
  loadExams()
}

async function loadExams() {
  examsLoading.value = true
  try {
    examRecords.value = await getTeacherStudentExams(classId, selectedStudent.value.user_id, { days: examDays.value })
  } finally {
    examsLoading.value = false
  }
}

function formatDate(str) {
  if (!str) return '—'
  return str.substring(0, 10)
}

onMounted(loadData)
</script>

<style scoped>
.score-pass { color: #00A60E; font-weight: 600; }
.score-fail { color: #D92916; font-weight: 600; }

.op-btn {
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 12px !important;
  color: #1865F2 !important;
  background: #EBF0FF !important;
  border-color: #B8D1FB !important;
  border-radius: 4px !important;
}
.op-btn:hover { color: #fff !important; background: #1865F2 !important; }
</style>
