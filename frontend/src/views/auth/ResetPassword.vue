<template>
  <div class="auth-page">
    <div class="auth-card">
      <div style="text-align: center; margin-bottom: 8px; font-size: 40px">🔑</div>
      <h2>重置密码</h2>
      <el-form :model="form" @submit.prevent="handleReset">
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
          <el-input v-model="form.new_password" type="password" placeholder="新密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%; height: 44px; font-size: 16px">重置密码</el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; margin-top: 8px">
        <router-link to="/login" style="color: #6366f1; text-decoration: none; font-size: 14px">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPassword, sendSms } from '../../api/auth'

const router = useRouter()
const loading = ref(false)
const countdown = ref(0)
const form = ref({ phone: '', code: '', new_password: '' })

async function handleSendCode() {
  if (!form.value.phone || form.value.phone.length !== 11) {
    return ElMessage.warning('请输入正确的手机号')
  }
  await sendSms({ phone: form.value.phone, purpose: 'reset_password' })
  ElMessage.success('验证码已发送')
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

async function handleReset() {
  if (!form.value.phone || !form.value.code || !form.value.new_password) {
    return ElMessage.warning('请填写完整信息')
  }
  loading.value = true
  try {
    await resetPassword(form.value)
    ElMessage.success('密码重置成功，请重新登录')
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
</style>
