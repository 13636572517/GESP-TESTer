<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="brand-mark">G</div>
        <h2>GESP考试训练平台</h2>
      </div>
      <el-tabs v-model="loginType">
        <el-tab-pane label="账号登录" name="username">
          <el-form :model="usernameForm" @submit.prevent="handleUsernameLogin">
            <el-form-item>
              <el-input v-model="usernameForm.username" placeholder="用户名" :prefix-icon="User" clearable />
            </el-form-item>
            <el-form-item>
              <el-input v-model="usernameForm.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; height: 44px; font-size: 16px">登录</el-button>
            </el-form-item>
          </el-form>
          <div style="text-align: center; font-size: 13px; color: #9CA3AF; margin-top: -4px">
            账号由管理员创建，如需账号请联系管理员
          </div>
        </el-tab-pane>
        <el-tab-pane label="手机号登录" name="password">
          <el-form :model="form" @submit.prevent="handleLogin">
            <el-form-item>
              <el-input v-model="form.phone" placeholder="手机号" :prefix-icon="Phone" maxlength="11" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; height: 44px; font-size: 16px">登录</el-button>
            </el-form-item>
          </el-form>
          <div class="auth-links">
            <router-link to="/register">注册账号</router-link>
            <router-link to="/reset-password">忘记密码</router-link>
          </div>
        </el-tab-pane>
        <el-tab-pane label="验证码登录" name="sms">
          <el-form :model="smsForm" @submit.prevent="handleSmsLogin">
            <el-form-item>
              <el-input v-model="smsForm.phone" placeholder="手机号" :prefix-icon="Phone" maxlength="11" />
            </el-form-item>
            <el-form-item>
              <div style="display: flex; gap: 8px; width: 100%">
                <el-input v-model="smsForm.code" placeholder="验证码" maxlength="6" />
                <el-button @click="sendCode('login')" :disabled="countdown > 0">
                  {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; height: 44px; font-size: 16px">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Phone, Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { loginByPassword, loginBySms, loginByUsername, sendSms } from '../../api/auth'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const loginType = ref('username')
const countdown = ref(0)

const usernameForm = ref({ username: '', password: '' })
const form = ref({ phone: '', password: '' })
const smsForm = ref({ phone: '', code: '' })

async function handleUsernameLogin() {
  if (!usernameForm.value.username || !usernameForm.value.password) {
    return ElMessage.warning('请填写用户名和密码')
  }
  loading.value = true
  try {
    const data = await loginByUsername(usernameForm.value)
    userStore.setTokens(data.access, data.refresh)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  if (!form.value.phone || !form.value.password) {
    return ElMessage.warning('请填写手机号和密码')
  }
  loading.value = true
  try {
    const data = await loginByPassword(form.value)
    userStore.setTokens(data.access, data.refresh)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function handleSmsLogin() {
  if (!smsForm.value.phone || !smsForm.value.code) {
    return ElMessage.warning('请填写手机号和验证码')
  }
  loading.value = true
  try {
    const data = await loginBySms(smsForm.value)
    userStore.setTokens(data.access, data.refresh)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function sendCode(purpose) {
  const phone = purpose === 'login' ? smsForm.value.phone : form.value.phone
  if (!phone || phone.length !== 11) {
    return ElMessage.warning('请输入正确的手机号')
  }
  await sendSms({ phone, purpose })
  ElMessage.success('验证码已发送')
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F7F8FA;
}
.auth-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border-top: 4px solid #1865F2;
}
.auth-brand {
  text-align: center;
  margin-bottom: 24px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #1865F2;
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.auth-card h2 {
  text-align: center;
  color: #21242C;
  font-size: 22px;
  margin: 0;
}
.auth-links {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}
.auth-links a {
  color: #1865F2;
  text-decoration: none;
  font-size: 14px;
}
.auth-links a:hover {
  color: #1551C9;
}
</style>
