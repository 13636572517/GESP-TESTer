<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-sidebar">
      <div class="logo" @click="$router.push('/')">
        <div class="logo-mark">G</div>
        <span v-show="!isCollapse" class="logo-text">GESP训练</span>
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
        <el-menu-item index="/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>学习统计</span>
        </el-menu-item>

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
  overflow: hidden;
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
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #1865F2;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
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
