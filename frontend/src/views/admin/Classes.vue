<template>
  <div class="page-container">
    <h1 class="page-title">班级管理</h1>

    <el-row :gutter="16">
      <!-- 左：班级列表 -->
      <el-col :span="9">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>班级列表</span>
              <el-button type="primary" size="small" @click="showCreate">创建班级</el-button>
            </div>
          </template>

          <div v-for="cls in classrooms" :key="cls.id"
            :class="['class-item', selectedClass?.id === cls.id && 'active']"
            @click="selectClass(cls)">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <div>
                <div class="class-name">{{ cls.name }}</div>
                <div class="class-meta">
                  <el-tag size="small" type="info" v-if="cls.level_name">{{ cls.level_name }}</el-tag>
                  <span style="font-size: 12px; color: #9CA3AF; margin-left: 6px">{{ cls.member_count }} 人</span>
                </div>
                <div v-if="cls.teacher_names?.length" style="font-size: 12px; color: #6B7280; margin-top: 4px">
                  老师：{{ cls.teacher_names.join('、') }}
                </div>
              </div>
              <div style="display: flex; gap: 4px" @click.stop>
                <el-button class="op-btn op-edit" size="small" @click="showEdit(cls)">编辑</el-button>
                <el-button class="op-btn op-delete" size="small" @click="handleDelete(cls)">删除</el-button>
              </div>
            </div>
            <div v-if="cls.description" class="class-desc">{{ cls.description }}</div>
          </div>

          <el-empty v-if="classrooms.length === 0" description="暂无班级" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右：班级成员 -->
      <el-col :span="15">
        <el-card v-if="selectedClass">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ selectedClass.name }} · 成员管理</span>
              <el-button type="primary" size="small" @click="addMemberVisible = true">
                <el-icon><Plus /></el-icon> 添加学员
              </el-button>
            </div>
          </template>

          <el-table :data="members" stripe v-loading="membersLoading" size="small">
            <el-table-column prop="phone" label="手机号" width="130" />
            <el-table-column prop="nickname" label="昵称" width="110" show-overflow-tooltip />
            <el-table-column label="级别" width="70">
              <template #default="{ row }">
                <el-tag size="small">{{ row.current_level }}级</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="备注" min-width="120" show-overflow-tooltip />
            <el-table-column prop="joined_at" label="加入时间" width="140">
              <template #default="{ row }">{{ formatDate(row.joined_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="60" fixed="right">
              <template #default="{ row }">
                <el-button class="op-btn op-delete" size="small" @click="handleRemoveMember(row)">移出</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="members.length === 0 && !membersLoading" description="班级暂无成员" :image-size="60" />
        </el-card>
        <el-card v-else>
          <el-empty description="请从左侧选择一个班级" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑班级弹窗 -->
    <el-dialog v-model="classDialogVisible" :title="editingClass ? '编辑班级' : '创建班级'" width="440px">
      <el-form :model="classForm" label-width="80px">
        <el-form-item label="班级名称">
          <el-input v-model="classForm.name" placeholder="如 2025年春季一级班" />
        </el-form-item>
        <el-form-item label="对应级别">
          <el-select v-model="classForm.level" clearable placeholder="不限" style="width: 100%">
            <el-option v-for="i in 8" :key="i" :label="`GESP ${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="classForm.description" type="textarea" :rows="2" placeholder="可选备注" />
        </el-form-item>
        <el-form-item label="授课老师">
          <el-select
            v-model="classForm.teacher_ids"
            multiple
            filterable
            placeholder="选择老师（可多选）"
            style="width: 100%"
          >
            <el-option
              v-for="t in teacherOptions"
              :key="t.id"
              :label="`${t.nickname || t.username}${t.phone ? ' · ' + t.phone : ''}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="classForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="classSaving" @click="handleSaveClass">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员弹窗 -->
    <el-dialog v-model="addMemberVisible" title="添加学员" width="420px">
      <el-form label-width="80px">
        <el-form-item label="搜索学员">
          <el-select
            v-model="selectedUserId"
            filterable
            remote
            reserve-keyword
            placeholder="输入手机号或昵称搜索"
            :remote-method="searchUsers"
            :loading="searchingUsers"
            style="width: 100%"
          >
            <el-option
              v-for="u in userOptions"
              :key="u.id"
              :label="`${u.profile?.nickname || u.username}（${u.profile?.phone || u.username}）`"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addNote" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMemberVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingMember" @click="handleAddMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getClassrooms, createClassroom, updateClassroom, deleteClassroom,
  getClassroomMembers, addClassroomMember, removeClassroomMember,
  getAdminUsers, getTeacherUsers,
} from '../../api/admin'

const classrooms = ref([])
const selectedClass = ref(null)
const members = ref([])
const membersLoading = ref(false)

// 班级表单
const classDialogVisible = ref(false)
const editingClass = ref(null)
const classSaving = ref(false)
const classForm = ref({ name: '', description: '', level: null, is_active: true, teacher_ids: [] })
const teacherOptions = ref([])

// 添加成员
const addMemberVisible = ref(false)
const selectedUserId = ref(null)
const addNote = ref('')
const addingMember = ref(false)
const userOptions = ref([])
const searchingUsers = ref(false)

async function searchUsers(query) {
  if (!query) { userOptions.value = []; return }
  searchingUsers.value = true
  try {
    const res = await getAdminUsers({ search: query, page_size: 20 })
    userOptions.value = res.results || res
  } finally {
    searchingUsers.value = false
  }
}

async function loadClassrooms() {
  const res = await getClassrooms()
  classrooms.value = res
}

async function loadTeacherOptions() {
  try {
    const res = await getTeacherUsers()
    // 管理员也可以担任老师
    const adminRes = await getAdminUsers({ is_admin: 'true', page_size: 100 })
    const all = [...(res.results || res), ...(adminRes.results || [])]
    const seen = new Set()
    teacherOptions.value = all.filter(u => {
      if (seen.has(u.id)) return false
      seen.add(u.id)
      return true
    })
  } catch { /* ignore */ }
}

async function selectClass(cls) {
  selectedClass.value = cls
  membersLoading.value = true
  try {
    members.value = await getClassroomMembers(cls.id)
  } finally {
    membersLoading.value = false
  }
}

function showCreate() {
  editingClass.value = null
  classForm.value = { name: '', description: '', level: null, is_active: true, teacher_ids: [] }
  classDialogVisible.value = true
}

function showEdit(cls) {
  editingClass.value = cls
  classForm.value = {
    name: cls.name,
    description: cls.description,
    level: cls.level || null,
    is_active: cls.is_active,
    teacher_ids: cls.teacher_ids || [],
  }
  classDialogVisible.value = true
}

async function handleSaveClass() {
  if (!classForm.value.name.trim()) {
    ElMessage.warning('请填写班级名称')
    return
  }
  classSaving.value = true
  try {
    const payload = {
      name: classForm.value.name.trim(),
      description: classForm.value.description.trim(),
      level: classForm.value.level || null,
      is_active: classForm.value.is_active,
      teacher_ids: classForm.value.teacher_ids,
    }
    if (editingClass.value) {
      await updateClassroom(editingClass.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createClassroom(payload)
      ElMessage.success('创建成功')
    }
    classDialogVisible.value = false
    await loadClassrooms()
    // refresh selected if edited
    if (editingClass.value && selectedClass.value?.id === editingClass.value.id) {
      selectedClass.value = classrooms.value.find(c => c.id === editingClass.value.id)
    }
  } finally {
    classSaving.value = false
  }
}

async function handleDelete(cls) {
  await ElMessageBox.confirm(`确定删除班级「${cls.name}」？成员关系将一并清除。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
  await deleteClassroom(cls.id)
  ElMessage.success('已删除')
  if (selectedClass.value?.id === cls.id) {
    selectedClass.value = null
    members.value = []
  }
  loadClassrooms()
}

async function handleAddMember() {
  if (!selectedUserId.value) {
    ElMessage.warning('请搜索并选择学员')
    return
  }
  addingMember.value = true
  try {
    const member = await addClassroomMember(selectedClass.value.id, {
      user_id: selectedUserId.value,
      note: addNote.value.trim(),
    })
    members.value.push(member)
    const cls = classrooms.value.find(c => c.id === selectedClass.value.id)
    if (cls) cls.member_count++
    ElMessage.success('添加成功')
    addMemberVisible.value = false
    selectedUserId.value = null
    addNote.value = ''
    userOptions.value = []
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    addingMember.value = false
  }
}

async function handleRemoveMember(member) {
  await ElMessageBox.confirm(`确定将「${member.nickname || member.phone}」移出班级？`, '移出确认', {
    type: 'warning',
    confirmButtonText: '确定移出',
    cancelButtonText: '取消',
  })
  await removeClassroomMember(selectedClass.value.id, member.id)
  members.value = members.value.filter(m => m.id !== member.id)
  const cls = classrooms.value.find(c => c.id === selectedClass.value.id)
  if (cls) cls.member_count--
  ElMessage.success('已移出')
}

function formatDate(str) {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

onMounted(() => {
  loadClassrooms()
  loadTeacherOptions()
})
</script>

<style scoped>
.class-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  border: 1px solid #E5E7EB;
  transition: all 0.15s;
}
.class-item:hover { border-color: #B8D1FB; background: #F8FAFF; }
.class-item.active { border-color: #1865F2; background: #EBF0FF; }
.class-name { font-weight: 600; font-size: 14px; color: #21242C; }
.class-meta { margin-top: 4px; display: flex; align-items: center; }
.class-desc { font-size: 12px; color: #9CA3AF; margin-top: 4px; }

.op-btn {
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
}
.op-edit { color: #1865F2 !important; background: #EBF0FF !important; border-color: #B8D1FB !important; }
.op-edit:hover { color: #1551C9 !important; background: #D6E4FF !important; border-color: #1865F2 !important; }
.op-delete { color: #C0392B !important; background: #FEF2F2 !important; border-color: #FECACA !important; }
.op-delete:hover { color: #991B1B !important; background: #FEE2E2 !important; border-color: #F87171 !important; }
</style>
