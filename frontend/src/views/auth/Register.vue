<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="brand-mark">G</div>
        <h2>注册账号</h2>
      </div>
      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input v-model="form.phone" placeholder="手机号" maxlength="11" />
        </el-form-item>
        <el-form-item>
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="form.code" placeholder="验证码" maxlength="6" />
            <el-button @click="handleSendCode" :disabled="countdown > 0">
              {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="设置密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.nickname" placeholder="昵称（选填）" maxlength="50" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; height: 44px; font-size: 16px">注册</el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; margin-top: 8px">
        <router-link to="/login" style="color: #1865F2; text-decoration: none; font-size: 14px">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerUser, sendSms } from '../../api/auth'

const router = useRouter()
const loading = ref(false)
const countdown = ref(0)
const form = ref({ phone: '', code: '', password: '', nickname: '' })

async function handleSendCode() {
  if (!form.value.phone || form.value.phone.length !== 11) {
    return ElMessage.warning('请输入正确的手机号')
  }
  await sendSms({ phone: form.value.phone, purpose: 'register' })
  ElMessage.success('验证码已发送')
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

async function handleRegister() {
  if (!form.value.phone || !form.value.code || !form.value.password) {
    return ElMessage.warning('请填写完整信息')
  }
  loading.value = true
  try {
    await registerUser(form.value)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
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
</style>
