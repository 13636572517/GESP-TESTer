<template>
  <div class="page-container">
    <h1 class="page-title">编程题</h1>

    <el-card style="margin-bottom: 16px">
      <el-form inline>
        <el-form-item label="级别">
          <el-select v-model="filterLevel" clearable placeholder="全部" @change="load">
            <el-option v-for="i in 8" :key="i" :label="`${i}级`" :value="i" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-empty v-if="!loading && questions.length === 0" description="暂无编程题" />
      <el-table v-else :data="questions" style="width: 100%" @row-click="goDetail">
        <el-table-column label="题目" prop="title" />
        <el-table-column label="级别" width="80">
          <template #default="{ row }">{{ row.level_id }}级</template>
        </el-table-column>
        <el-table-column label="难度" width="90">
          <template #default="{ row }">
            <el-tag :type="diffType(row.difficulty)" size="small">{{ row.difficulty_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间限制" width="100">
          <template #default="{ row }">{{ row.time_limit }}ms</template>
        </el-table-column>
        <el-table-column label="内存限制" width="100">
          <template #default="{ row }">{{ row.memory_limit }}MB</template>
        </el-table-column>
        <el-table-column label="" width="80">
          <template #default>
            <el-icon><ArrowRight /></el-icon>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import request from '../../utils/request'

const router = useRouter()
const loading = ref(false)
const questions = ref([])
const filterLevel = ref(null)

function diffType(d) {
  return { 1: 'success', 2: 'warning', 3: 'danger' }[d] ?? ''
}

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filterLevel.value) params.level = filterLevel.value
    const res = await request.get('/programming/questions/', { params })
    questions.value = res
  } finally {
    loading.value = false
  }
}

function goDetail(row) {
  router.push(`/programming/${row.id}`)
}

onMounted(load)
</script>

<style scoped>
:deep(.el-table__row) { cursor: pointer; }
</style>
