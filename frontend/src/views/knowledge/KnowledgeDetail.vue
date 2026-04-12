<template>
  <div class="page-container">
    <el-page-header @back="$router.back()">
      <template #content>
        <span>{{ detail.name }}</span>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px" v-if="detail.name">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <div>
            <el-tag size="small" style="margin-right: 8px">{{ detail.level_name }}</el-tag>
            <el-tag size="small" type="info">{{ detail.chapter_name }}</el-tag>
          </div>
          <el-button type="primary" size="small" @click="startKnowledgePractice">
            练习该知识点
          </el-button>
        </div>
      </template>

      <div v-if="detail.content" class="knowledge-content" v-html="detail.content" v-highlight></div>
      <el-empty v-else description="暂无讲解内容" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getKnowledgeDetail } from '../../api/knowledge'
import { startPractice } from '../../api/practice'

const route = useRoute()
const router = useRouter()
const detail = ref({})

async function startKnowledgePractice() {
  const data = await startPractice({
    session_type: 1,
    knowledge_ids: [Number(route.params.id)],
    count: 10,
  })
  router.push(`/practice/${data.session_id}`)
}

onMounted(async () => {
  detail.value = await getKnowledgeDetail(route.params.id)
})
</script>

<style scoped>
.knowledge-content {
  line-height: 1.8;
  font-size: 15px;
}
.knowledge-content :deep(img) {
  max-width: 100%;
}
</style>
