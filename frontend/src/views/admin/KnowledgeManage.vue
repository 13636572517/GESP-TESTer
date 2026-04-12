<template>
  <div class="page-container">
    <h1 class="page-title">知识点管理</h1>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>知识点树</template>
          <el-tree
            :data="treeData"
            :props="{ children: 'children', label: 'label' }"
            @node-click="handleNodeClick"
            highlight-current
            default-expand-all
          />
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-if="selectedPoint">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ selectedPoint.name }} - 讲解内容编辑</span>
              <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            </div>
          </template>
          <el-input
            v-model="content"
            type="textarea"
            :rows="20"
            placeholder="在此编辑知识点讲解内容，支持HTML格式和LaTeX公式"
          />
          <div style="margin-top: 12px; font-size: 13px; color: #909399">
            提示：可使用HTML标签格式化内容。LaTeX公式使用 $...$ 包裹（行内）或 $$...$$ 包裹（独立行）。
          </div>
        </el-card>
        <el-card v-else>
          <el-empty description="请从左侧选择一个知识点" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getKnowledgeTree, getKnowledgeDetail } from '../../api/knowledge'
import { updateKnowledgeContent } from '../../api/admin'

const tree = ref([])
const treeData = ref([])
const selectedPoint = ref(null)
const content = ref('')
const saving = ref(false)

function handleNodeClick(data) {
  if (data.type === 'point') {
    loadPointDetail(data.id)
  }
}

async function loadPointDetail(id) {
  const detail = await getKnowledgeDetail(id)
  selectedPoint.value = detail
  content.value = detail.content || ''
}

async function handleSave() {
  if (!selectedPoint.value) return
  saving.value = true
  try {
    await updateKnowledgeContent(selectedPoint.value.id, { content: content.value })
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  tree.value = await getKnowledgeTree()
  treeData.value = tree.value.map(level => ({
    label: level.name,
    type: 'level',
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
})
</script>
