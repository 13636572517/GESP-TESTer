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

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>知识点树</span>
          </template>
          <el-tree
            :data="filteredTreeData"
            :props="{ children: 'children', label: 'label' }"
            @node-click="handleNodeClick"
            highlight-current
            default-expand-all
          />
          <el-empty v-if="filteredTreeData.length === 0" description="该级别暂无知识点" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-if="selectedPoint">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <div>
                <span style="font-weight: 600; font-size: 16px">{{ selectedPoint.name }}</span>
                <el-tag size="small" style="margin-left: 8px">{{ selectedPoint.level_name }}</el-tag>
                <el-tag size="small" type="info" style="margin-left: 4px">{{ selectedPoint.chapter_name }}</el-tag>
              </div>
              <el-button type="primary" size="small" @click="startKnowledgePractice">
                练习该知识点
              </el-button>
            </div>
          </template>
          <div v-if="selectedPoint.content" class="knowledge-content" v-html="selectedPoint.content" v-highlight></div>
          <el-empty v-else description="暂无讲解内容" />
        </el-card>
        <el-card v-else>
          <el-empty description="请从左侧选择一个知识点" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLevels, getKnowledgeTree, getKnowledgeDetail } from '../../api/knowledge'
import { startPractice } from '../../api/practice'

const router = useRouter()
const levels = ref([])
const tree = ref([])
const treeData = ref([])
const activeLevel = ref('1')
const selectedPoint = ref(null)

const filteredTreeData = computed(() => {
  return treeData.value.filter(node => node.levelId === activeLevel.value)
})

function handleLevelChange() {
  selectedPoint.value = null
}

function handleNodeClick(data) {
  if (data.type === 'point') {
    loadPointDetail(data.id)
  }
}

async function loadPointDetail(id) {
  const detail = await getKnowledgeDetail(id)
  selectedPoint.value = detail
}

async function startKnowledgePractice() {
  if (!selectedPoint.value) return
  const data = await startPractice({
    session_type: 1,
    knowledge_ids: [selectedPoint.value.id],
    count: 10,
  })
  router.push(`/practice/${data.session_id}`)
}

async function refreshTree() {
  tree.value = await getKnowledgeTree()
  treeData.value = tree.value.map(level => ({
    label: level.name,
    type: 'level',
    levelId: String(level.id),
    children: (level.chapters || []).map(ch => ({
      label: ch.name,
      type: 'chapter',
      children: (ch.points || []).map(p => ({
        label: p.name,
        id: p.id,
        type: 'point',
      })),
    })),
  }))
}

onMounted(async () => {
  const res = await getLevels()
  levels.value = res.results || res
  await refreshTree()
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
