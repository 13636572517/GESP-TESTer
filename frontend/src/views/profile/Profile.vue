<template>
  <div class="page-container">
    <h1 class="page-title">个人中心</h1>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <div style="text-align: center">
            <el-upload
              :show-file-list="false"
              :before-upload="handleAvatarUpload"
              accept="image/*"
            >
              <el-avatar :size="80" :src="userStore.userInfo?.avatar || undefined" style="cursor: pointer; border: 3px solid #1865F2">
                {{ (userStore.userInfo?.nickname || 'U')[0] }}
              </el-avatar>
            </el-upload>
            <div style="margin-top: 12px; font-size: 18px; font-weight: 600">
              {{ userStore.userInfo?.nickname || '未设置昵称' }}
            </div>
            <div style="color: #6b7280; margin-top: 4px">
              {{ userStore.userInfo?.phone }}
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>基本信息</template>
          <el-form :model="profileForm" label-width="80px">
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" maxlength="50" />
            </el-form-item>
            <el-form-item label="学习级别">
              <el-select v-model="profileForm.current_level">
                <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateProfile">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>修改密码</template>
          <el-form :model="passwordForm" label-width="80px">
            <el-form-item label="原密码">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import request from '../../utils/request'

const userStore = useUserStore()

const profileForm = ref({ nickname: '', current_level: 1 })
const passwordForm = ref({ old_password: '', new_password: '' })

async function handleUpdateProfile() {
  await request.put('/user/profile/', profileForm.value)
  ElMessage.success('保存成功')
  userStore.fetchProfile()
}

async function handleChangePassword() {
  if (!passwordForm.value.old_password || !passwordForm.value.new_password) {
    return ElMessage.warning('请填写完整')
  }
  await request.put('/user/password/', passwordForm.value)
  ElMessage.success('密码修改成功')
  passwordForm.value = { old_password: '', new_password: '' }
}

async function handleAvatarUpload(file) {
  const formData = new FormData()
  formData.append('avatar', file)
  await request.post('/user/avatar/', formData)
  ElMessage.success('头像上传成功')
  userStore.fetchProfile()
  return false
}

onMounted(() => {
  if (userStore.userInfo) {
    profileForm.value.nickname = userStore.userInfo.nickname || ''
    profileForm.value.current_level = userStore.userInfo.current_level || 1
  }
})
</script>
