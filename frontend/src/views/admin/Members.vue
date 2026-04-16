<template>
  <div class="page-container">
    <h1 class="page-title">会员管理</h1>

    <!-- 搜索筛选栏 -->
    <el-card style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input v-model="search" clearable placeholder="手机号 / 昵称" style="width: 180px"
            @keyup.enter="loadUsers" @clear="loadUsers" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filterLevel" clearable placeholder="全部" style="width: 90px" @change="loadUsers">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filterAdmin" clearable placeholder="全部" style="width: 90px" @change="loadUsers">
            <el-option label="管理员" value="true" />
            <el-option label="普通用户" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadUsers"><el-icon><Search /></el-icon> 搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card>
      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="头像" width="60">
          <template #default="{ row }">
            <el-avatar :size="32" :src="row.avatar || undefined" style="background: #1865F2">
              {{ (row.nickname || row.phone || 'U')[0] }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="nickname" label="昵称" width="120" show-overflow-tooltip />
        <el-table-column label="级别" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.current_level }}级</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : ''" size="small">
              {{ row.is_admin ? '管理员' : '学员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="所在班级" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.class_names?.length">
              <el-tag v-for="n in row.class_names" :key="n" size="small" type="info" style="margin-right: 4px">{{ n }}</el-tag>
            </span>
            <span v-else style="color: #9CA3AF">未加入班级</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 4px">
              <el-button class="op-btn op-edit" size="small" @click="showEdit(row)">编辑</el-button>
              <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div style="display: flex; justify-content: flex-end; margin-top: 16px">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑用户" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="手机号">
          <el-input :value="editForm.phone" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        <el-form-item label="学习级别">
          <el-select v-model="editForm.current_level" style="width: 100%">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="editForm.is_admin" active-text="是" inactive-text="否" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getAdminUsers, updateAdminUser, deleteAdminUser } from '../../api/admin'

const users = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const filterLevel = ref(null)
const filterAdmin = ref(null)

const editVisible = ref(false)
const saving = ref(false)
const editForm = ref({})
const editId = ref(null)

async function loadUsers() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (search.value) params.search = search.value
    if (filterLevel.value) params.level = filterLevel.value
    if (filterAdmin.value !== null && filterAdmin.value !== '') params.is_admin = filterAdmin.value
    const res = await getAdminUsers(params)
    users.value = res.results
    total.value = res.count
  } finally {
    loading.value = false
  }
}

function showEdit(row) {
  editId.value = row.id
  editForm.value = {
    phone: row.phone,
    nickname: row.nickname,
    current_level: row.current_level,
    is_admin: row.is_admin,
  }
  editVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    await updateAdminUser(editId.value, {
      nickname: editForm.value.nickname,
      current_level: editForm.value.current_level,
      is_admin: editForm.value.is_admin,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.nickname || row.phone}」？此操作不可恢复。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
  await deleteAdminUser(row.id)
  ElMessage.success('已删除')
  loadUsers()
}

function formatDate(str) {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

onMounted(loadUsers)
</script>

<style scoped>
.op-btn {
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
}
.op-edit {
  color: #1865F2 !important;
  background: #EBF0FF !important;
  border-color: #B8D1FB !important;
}
.op-edit:hover { color: #1551C9 !important; background: #D6E4FF !important; border-color: #1865F2 !important; }
.op-delete {
  color: #C0392B !important;
  background: #FEF2F2 !important;
  border-color: #FECACA !important;
}
.op-delete:hover { color: #991B1B !important; background: #FEE2E2 !important; border-color: #F87171 !important; }
</style>
