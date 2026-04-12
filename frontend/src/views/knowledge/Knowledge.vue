<template>
  <div class="page-container">
    <h1 class="page-title">知识点体系</h1>

    <el-tabs v-model="activeLevel" @tab-change="handleLevelChange">
      <el-tab-pane
        v-for="level in levels"
        :key="level.id"
        :label="level.name"
        :name="String(level.id)"
      />
    </el-tabs>

    <div v-if="tree.length > 0">
      <el-collapse v-model="activeChapters">
        <el-collapse-item
          v-for="chapter in currentChapters"
          :key="chapter.id"
          :title="chapter.name"
          :name="chapter.id"
        >
          <div
            v-for="point in chapter.points"
            :key="point.id"
            class="knowledge-item"
            @click="$router.push(`/knowledge/${point.id}`)"
          >
            <span>{{ point.name }}</span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-empty v-else description="加载中..." />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getKnowledgeTree, getLevels } from '../../api/knowledge'

const levels = ref([])
const tree = ref([])
const activeLevel = ref('1')
const activeChapters = ref([])

const currentChapters = computed(() => {
  const level = tree.value.find(l => String(l.id) === activeLevel.value)
  return level?.chapters || []
})

function handleLevelChange() {
  activeChapters.value = []
}

onMounted(async () => {
  levels.value = await getLevels()
  tree.value = await getKnowledgeTree()
})
</script>

<style scoped>
.knowledge-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
}
.knowledge-item:hover {
  background: #f5f7fa;
}
</style>
