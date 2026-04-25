<template>
  <div class="page-container">
    <h1 class="page-title">我的班级</h1>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="8" v-for="cls in classes" :key="cls.id" style="margin-bottom: 16px">
        <el-card class="class-card" shadow="hover" @click="$router.push(`/teacher/classes/${cls.id}`)">
          <div class="class-card-header">
            <span class="class-name">{{ cls.name }}</span>
            <el-tag v-if="cls.level_name" size="small" type="info">{{ cls.level_name }}</el-tag>
          </div>
          <div class="class-desc" v-if="cls.description">{{ cls.description }}</div>
          <div class="class-meta">
            <span><el-icon><User /></el-icon> {{ cls.member_count }} 名学员</span>
            <el-tag :type="cls.is_active ? 'success' : 'info'" size="small">{{ cls.is_active ? '进行中' : '已结束' }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && classes.length === 0" description="暂未分配班级" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User } from '@element-plus/icons-vue'
import { getTeacherClasses } from '../../api/admin'

const classes = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    classes.value = await getTeacherClasses()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.class-card {
  cursor: pointer;
  transition: transform 0.15s;
}
.class-card:hover { transform: translateY(-2px); }
.class-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.class-name { font-weight: 600; font-size: 16px; color: #21242C; }
.class-desc { font-size: 13px; color: #6B7280; margin-bottom: 10px; }
.class-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #6B7280;
  margin-top: 8px;
}
.class-meta .el-icon { vertical-align: middle; margin-right: 4px; }
</style>
