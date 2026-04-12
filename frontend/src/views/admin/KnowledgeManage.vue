<template>
  <div class="page-container">
    <h1 class="page-title">知识点管理</h1>

    <!-- 级别选择标签 -->
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
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>知识点树</span>
              <div>
                <el-dropdown @command="handleImportCommand" style="margin-right: 8px">
                  <el-button size="small" type="primary">
                    导入 <el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="csv">CSV文件导入</el-dropdown-item>
                      <el-dropdown-item command="template">下载CSV模板</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button size="small" @click="handleExport">导出</el-button>
              </div>
            </div>
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

    <!-- CSV导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="CSV导入知识点" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".csv"
        :on-change="handleFileChange"
        :on-exceed="() => ElMessage.warning('只能上传一个文件')"
        drag
      >
        <el-icon style="font-size: 40px; color: #909399"><upload-filled /></el-icon>
        <div style="margin-top: 8px">将CSV文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div style="color: #909399; font-size: 12px; margin-top: 8px">
            仅支持 .csv 格式，编码 UTF-8 或 GBK。
            列：级别、章节、知识点、描述(选填)、内容(选填)、排序(选填)
          </div>
        </template>
      </el-upload>

      <!-- 导入结果 -->
      <div v-if="importResult" style="margin-top: 16px; padding: 12px; background: #f5f7fa; border-radius: 6px">
        <div><strong>导入完成</strong></div>
        <div style="margin-top: 8px">
          新建: <el-tag type="success" size="small">{{ importResult.created_count }}</el-tag>
          更新: <el-tag type="warning" size="small">{{ importResult.updated_count }}</el-tag>
          失败: <el-tag type="danger" size="small">{{ importResult.error_count }}</el-tag>
        </div>
        <div v-if="importResult.errors && importResult.errors.length" style="margin-top: 8px; max-height: 150px; overflow-y: auto">
          <div v-for="(err, idx) in importResult.errors" :key="idx" style="color: #f56c6c; font-size: 12px">
            第{{ err.row }}行: {{ err.error }}
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleImportSubmit" :loading="importing" :disabled="!importFile">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, UploadFilled } from '@element-plus/icons-vue'
import { getLevels, getKnowledgeTree, getKnowledgeDetail } from '../../api/knowledge'
import {
  updateKnowledgeContent,
  importKnowledgeCsv,
  downloadKnowledgeCsvTemplate,
  exportKnowledgeCsv,
} from '../../api/admin'

const levels = ref([])
const tree = ref([])
const treeData = ref([])
const activeLevel = ref('1')
const selectedPoint = ref(null)
const content = ref('')
const saving = ref(false)

const filteredTreeData = computed(() => {
  return treeData.value.filter(node => node.levelId === activeLevel.value)
})

// Import state
const importDialogVisible = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const uploadRef = ref(null)

function handleLevelChange() {
  selectedPoint.value = null
  content.value = ''
}

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

function handleImportCommand(cmd) {
  if (cmd === 'csv') {
    importFile.value = null
    importResult.value = null
    importDialogVisible.value = true
  } else if (cmd === 'template') {
    downloadTemplate()
  }
}

function handleFileChange(file) {
  importFile.value = file.raw
}

async function handleImportSubmit() {
  if (!importFile.value) return
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const res = await importKnowledgeCsv(formData)
    importResult.value = res
    if (res.created_count > 0 || res.updated_count > 0) {
      ElMessage.success(`导入成功：新建${res.created_count}个，更新${res.updated_count}个`)
      await refreshTree()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

async function downloadTemplate() {
  try {
    const res = await downloadKnowledgeCsvTemplate()
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'knowledge_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载模板失败')
  }
}

async function handleExport() {
  try {
    const res = await exportKnowledgeCsv({ level: activeLevel.value })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    const levelName = levels.value.find(l => String(l.id) === activeLevel.value)?.name || ''
    a.download = `knowledge_export_${levelName}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
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
