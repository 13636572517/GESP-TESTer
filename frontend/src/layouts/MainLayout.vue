<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-sidebar">
      <div class="logo" @click="$router.push('/')">
        <img src="/yusuan_logo_192.png" class="logo-mark" alt="御算" />
        <span v-show="!isCollapse" class="logo-text">御算·LOGOS</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        router
        background-color="transparent"
        text-color="#21242C"
        active-text-color="#1865F2"
        class="sidebar-menu"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识点</span>
        </el-menu-item>
        <el-menu-item index="/practice">
          <el-icon><EditPen /></el-icon>
          <span>练习</span>
        </el-menu-item>
        <el-menu-item index="/exam">
          <el-icon><Timer /></el-icon>
          <span>模拟考试</span>
        </el-menu-item>
        <el-menu-item index="/mistakes">
          <el-icon><Warning /></el-icon>
          <span>错题本</span>
        </el-menu-item>
        <el-menu-item index="/programming">
          <el-icon><Monitor /></el-icon>
          <span>编程题</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>学习统计</span>
        </el-menu-item>

        <el-sub-menu index="teacher" v-if="userStore.isTeacher || userStore.isAdmin">
          <template #title>
            <el-icon><School /></el-icon>
            <span>教师中心</span>
          </template>
          <el-menu-item index="/teacher/classes">我的班级</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="admin" v-if="userStore.isAdmin">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>管理</span>
          </template>
          <el-menu-item index="/admin/questions">题目管理</el-menu-item>
          <el-menu-item index="/admin/pdf-import">PDF导入题目</el-menu-item>
          <el-menu-item index="/admin/knowledge">知识点管理</el-menu-item>
          <el-menu-item index="/admin/exam-templates">试卷管理</el-menu-item>
          <el-menu-item index="/admin/members">会员管理</el-menu-item>
          <el-menu-item index="/admin/classes">班级管理</el-menu-item>
          <el-menu-item index="/admin/ai-questions">AI 题目工具</el-menu-item>
          <el-menu-item index="/admin/feedbacks">题目反馈</el-menu-item>
          <el-menu-item index="/admin/programming">编程题管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <el-icon style="cursor: pointer; font-size: 20px; color: #6B7280" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <div style="display: flex; align-items: center; gap: 16px">
          <span style="color: #21242C; font-weight: 600">{{ userStore.userInfo?.nickname || '用户' }}</span>
          <el-dropdown>
            <el-avatar :size="36" :src="userStore.userInfo?.avatar || undefined" style="cursor: pointer; background: #1865F2">
              {{ (userStore.userInfo?.nickname || 'U')[0] }}
            </el-avatar>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item @click="$router.push('/ai-settings')">我的 AI 设置</el-dropdown-item>
                <el-dropdown-item @click="$router.push('/my-feedbacks')">我的反馈</el-dropdown-item>
                <template v-if="userStore.isAdmin">
                  <el-dropdown-item divided @click="$router.push('/admin/ai-settings')">管理员 AI 设置</el-dropdown-item>
                </template>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main style="background: #F7F8FA; overflow-y: auto">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const router = useRouter()
const isCollapse = ref(false)

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-sidebar {
  background: #fff;
  border-right: 1px solid #E5E7EB;
  transition: width 0.3s;
  overflow-x: hidden;
  overflow-y: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  border-bottom: 1px solid #E5E7EB;
}
.logo-mark {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  object-fit: contain;
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #21242C;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #E5E7EB;
}

/* 菜单整体 */
.sidebar-menu {
  border-right: none !important;
  padding: 8px;
}

/* 菜单项默认样式 */
.sidebar-menu .el-menu-item {
  border-radius: 8px !important;
  margin: 2px 0;
  height: 44px;
  line-height: 44px;
  transition: all 0.2s;
}
.sidebar-menu .el-menu-item:hover {
  background: #F7F8FA !important;
  color: #1865F2 !important;
}

/* 选中态：浅蓝背景 + 蓝色文字 */
.sidebar-menu .el-menu-item.is-active {
  background: #EBF0FF !important;
  color: #1865F2 !important;
  font-weight: 600;
  border-left: 3px solid #1865F2;
}
.sidebar-menu .el-menu-item.is-active .el-icon {
  color: #1865F2 !important;
}

/* 子菜单 */
.sidebar-menu .el-sub-menu :deep(.el-sub-menu__title) {
  border-radius: 8px !important;
  margin: 2px 0;
  height: 44px;
  line-height: 44px;
}
.sidebar-menu .el-sub-menu :deep(.el-sub-menu__title:hover) {
  background: #F7F8FA !important;
}
</style>
