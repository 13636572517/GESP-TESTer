<template>
  <div class="auth-page">
    <div class="auth-card">
      <div style="text-align: center; margin-bottom: 8px; font-size: 40px">🎯</div>
      <h2>GESP考试训练平台</h2>
      <el-tabs v-model="loginType">
        <el-tab-pane label="密码登录" name="password">
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
      <div class="auth-links">
        <router-link to="/register">注册账号</router-link>
        <router-link to="/reset-password">忘记密码</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Phone, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { loginByPassword, loginBySms, sendSms } from '../../api/auth'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const loginType = ref('password')
const countdown = ref(0)

const form = ref({ phone: '', password: '' })
const smsForm = ref({ phone: '', code: '' })

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
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
}
.auth-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border-top: 4px solid #6366f1;
}
.auth-card h2 {
  text-align: center;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 22px;
}
.auth-links {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}
.auth-links a {
  color: #6366f1;
  text-decoration: none;
  font-size: 14px;
}
.auth-links a:hover {
  color: #4f46e5;
}
</style>
