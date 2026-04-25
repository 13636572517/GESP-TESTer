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

    <!-- 操作栏 -->
    <div style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 12px">
      <el-button @click="handleExport">导出选中</el-button>
      <el-button @click="handleExportAll">导出全部</el-button>
      <el-button @click="importDialogVisible = true">导入</el-button>
      <el-button type="primary" @click="showCreate">
        <el-icon><Plus /></el-icon> 新建账号
      </el-button>
    </div>

    <!-- 用户列表 -->
    <el-card>
      <el-table :data="users" stripe v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="头像" width="56">
          <template #default="{ row }">
            <el-avatar :size="32" :src="row.avatar || undefined" style="background: #1865F2">
              {{ (row.nickname || row.username || row.phone || 'U')[0] }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column label="账号 / 手机号" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.username" style="font-family: monospace; font-size: 13px">{{ row.username }}</div>
            <div v-if="row.phone" style="color: #6B7280; font-size: 12px">{{ row.phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120" show-overflow-tooltip />
        <el-table-column label="级别" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.current_level }}级</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
            <el-tag v-else-if="row.is_teacher" type="warning" size="small">老师</el-tag>
            <el-tag v-else size="small">学员</el-tag>
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
    <el-dialog v-model="editVisible" title="编辑用户" width="420px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item v-if="editForm.username" label="用户名">
          <el-input :value="editForm.username" disabled />
        </el-form-item>
        <el-form-item v-if="editForm.phone" label="手机号">
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
        <el-form-item label="老师">
          <el-switch v-model="editForm.is_teacher" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-divider content-position="left" style="margin: 8px 0">重置密码（选填）</el-divider>
        <el-form-item label="新密码">
          <el-input v-model="editForm.new_password" type="password" show-password placeholder="留空则不修改密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="批量导入会员" width="500px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px">
        CSV格式：用户名、手机号、昵称、学习级别、是否管理员（是/否）<br>
        已存在的用户名自动跳过。
      </el-alert>
      <el-form label-width="90px">
        <el-form-item label="默认密码">
          <el-input v-model="defaultPassword" placeholder="导入账号的初始密码（至少6位）" style="width:200px" />
        </el-form-item>
        <el-form-item label="CSV文件">
          <el-upload :auto-upload="false" :on-change="onImportFileChange" :show-file-list="false" accept=".csv">
            <el-button>选择文件</el-button>
          </el-upload>
          <span v-if="importFile" style="margin-left:8px;font-size:12px;color:#6B7280">{{ importFile.name }}</span>
        </el-form-item>
      </el-form>
      <div v-if="importResult" style="margin-top:8px">
        <el-alert :type="importResult.error_count > 0 ? 'warning' : 'success'" :closable="false">
          创建 {{ importResult.created_count }} 人，跳过 {{ importResult.skip_count }} 人，失败 {{ importResult.error_count }} 人
          <span v-if="importResult.created_count > 0">（初始密码：{{ importResult.default_password }}）</span>
        </el-alert>
        <div v-for="err in importResult.errors" :key="err.row" style="font-size:12px;color:#f56c6c;margin-top:4px">
          第 {{ err.row }} 行：{{ err.error }}
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importing" :disabled="!importFile" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 新建账号弹窗 -->
    <el-dialog v-model="createVisible" title="新建账号" width="420px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="登录时使用的用户名" clearable />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="createForm.nickname" placeholder="不填则同用户名" />
        </el-form-item>
        <el-form-item label="学习级别">
          <el-select v-model="createForm.current_level" style="width: 100%">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="createForm.is_admin" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="老师">
          <el-switch v-model="createForm.is_teacher" active-text="是" inactive-text="否" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser, exportAdminUsers, importAdminUsers } from '../../api/admin'

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

const createVisible = ref(false)
const creating = ref(false)
const createForm = ref({ username: '', password: '', nickname: '', current_level: 1, is_admin: false, is_teacher: false })

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

function showCreate() {
  createForm.value = { username: '', password: '', nickname: '', current_level: 1, is_admin: false, is_teacher: false }
  createVisible.value = true
}

async function handleCreate() {
  if (!createForm.value.username.trim()) return ElMessage.warning('请填写用户名')
  if (createForm.value.password.length < 6) return ElMessage.warning('密码至少6位')
  creating.value = true
  try {
    await createAdminUser(createForm.value)
    ElMessage.success('账号已创建')
    createVisible.value = false
    loadUsers()
  } finally {
    creating.value = false
  }
}

function showEdit(row) {
  editId.value = row.id
  editForm.value = {
    username: row.username,
    phone: row.phone,
    nickname: row.nickname,
    current_level: row.current_level,
    is_admin: row.is_admin,
    is_teacher: row.is_teacher,
    new_password: '',
  }
  editVisible.value = true
}

async function handleSave() {
  if (editForm.value.new_password && editForm.value.new_password.length < 6) {
    return ElMessage.warning('新密码至少6位')
  }
  saving.value = true
  try {
    const payload = {
      nickname: editForm.value.nickname,
      current_level: editForm.value.current_level,
      is_admin: editForm.value.is_admin,
      is_teacher: editForm.value.is_teacher,
    }
    if (editForm.value.new_password) payload.new_password = editForm.value.new_password
    await updateAdminUser(editId.value, payload)
    ElMessage.success('保存成功')
    editVisible.value = false
    loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.nickname || row.username || row.phone}」？此操作不可恢复。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
  await deleteAdminUser(row.id)
  ElMessage.success('已删除')
  loadUsers()
}

// ─── 导出 / 导入 ─────────────────────────────────────
const selectedRows = ref([])
const importDialogVisible = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const defaultPassword = ref('gesp123456')

function handleSelectionChange(rows) { selectedRows.value = rows }

function triggerBlobDownload(promise, filename) {
  promise.then(res => {
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载完成')
  }).catch(() => ElMessage.error('下载失败'))
}

function handleExport() {
  const ids = selectedRows.value.map(r => r.id)
  if (!ids.length) return ElMessage.warning('请先勾选要导出的会员')
  triggerBlobDownload(exportAdminUsers(ids), 'members.csv')
}

function handleExportAll() {
  triggerBlobDownload(exportAdminUsers([]), 'members.csv')
}

function onImportFileChange(file) { importFile.value = file.raw }

async function handleImport() {
  if (!importFile.value) return
  importing.value = true
  importResult.value = null
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    fd.append('default_password', defaultPassword.value || 'gesp123456')
    const res = await importAdminUsers(fd)
    importResult.value = res
    if (res.created_count > 0) { ElMessage.success(`成功导入 ${res.created_count} 名会员`); loadUsers() }
  } catch { ElMessage.error('导入失败') } finally { importing.value = false }
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
