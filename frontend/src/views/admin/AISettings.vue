<template>
  <div class="page-container">
    <h1 class="page-title">AI 设置</h1>

    <el-tabs v-model="activeTab" type="border-card">

      <!-- ── Tab 1：配置与测试 ── -->
      <el-tab-pane label="配置与测试" name="config">
        <div class="tab-body">

          <!-- API Key -->
          <el-card shadow="never" class="setting-card">
            <template #header>
              <span class="card-title">API Key</span>
              <el-tag :type="hasKey ? 'success' : 'danger'" size="small" style="margin-left:8px">
                {{ hasKey ? '已配置' : '未配置' }}
              </el-tag>
            </template>
            <el-form label-width="100px">
              <el-form-item label="来源">
                <el-tag v-if="configData.key_source === 'db'" type="success">管理页面已设置</el-tag>
                <el-tag v-else-if="configData.key_source === 'env'" type="warning">来自 .env 文件</el-tag>
                <el-tag v-else type="danger">未配置</el-tag>
                <span style="margin-left:8px;font-size:12px;color:#909399">
                  {{ configData.key_source === 'db' ? '在此页面设置的 Key 优先级最高' :
                     configData.key_source === 'env' ? '读取自 backend/.env 的 DASHSCOPE_API_KEY，可在此覆盖' :
                     '请在此设置 API Key，或在 backend/.env 中配置 DASHSCOPE_API_KEY' }}
                </span>
              </el-form-item>
              <el-form-item label="当前 Key">
                <span v-if="!editingKey" style="font-family:monospace;color:#606266">
                  {{ configData.api_key_masked || '（未设置）' }}
                </span>
                <el-input
                  v-else
                  v-model="newApiKey"
                  type="password"
                  show-password
                  placeholder="输入新的 API Key"
                  style="max-width:400px"
                />
                <el-button
                  link type="primary"
                  style="margin-left:12px"
                  @click="toggleEditKey"
                >{{ editingKey ? '取消' : '修改' }}</el-button>
                <el-button
                  v-if="configData.key_source === 'db' && !editingKey"
                  link type="danger"
                  style="margin-left:4px"
                  @click="handleClearKey"
                >清除（回退到 .env）</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 模型配置 -->
          <el-card shadow="never" class="setting-card">
            <template #header><span class="card-title">模型配置</span></template>
            <el-form label-width="100px">
              <el-form-item label="标注模型">
                <div style="display:flex;flex-direction:column;gap:6px">
                  <el-select v-model="configData.tag_model" style="width:340px" filterable allow-create default-first-option placeholder="选择模型">
                    <el-option-group v-for="g in modelGroups" :key="g.label" :label="g.label">
                      <el-option v-for="m in g.models" :key="m.value" :label="m.label" :value="m.value" />
                    </el-option-group>
                  </el-select>
                  <el-input v-model="configData.tag_model" style="width:340px" placeholder="或手动输入模型 Code，如 qwen3-235b-a22b" clearable />
                </div>
                <span class="field-hint">用于知识点 AI 批量标注</span>
              </el-form-item>
              <el-form-item label="出题模型">
                <div style="display:flex;flex-direction:column;gap:6px">
                  <el-select v-model="configData.gen_model" style="width:340px" filterable allow-create default-first-option placeholder="选择模型">
                    <el-option-group v-for="g in modelGroups" :key="g.label" :label="g.label">
                      <el-option v-for="m in g.models" :key="m.value" :label="m.label" :value="m.value" />
                    </el-option-group>
                  </el-select>
                  <el-input v-model="configData.gen_model" style="width:340px" placeholder="或手动输入模型 Code，如 qwen3-235b-a22b" clearable />
                </div>
                <span class="field-hint">用于 AI 题目生成</span>
              </el-form-item>
              <el-form-item label="">
                <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
                <span v-if="configData.updated_at" style="margin-left:16px;font-size:12px;color:#909399">
                  上次保存：{{ configData.updated_at }}
                </span>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 模型测试 -->
          <el-card shadow="never" class="setting-card">
            <template #header><span class="card-title">模型可用性测试</span></template>
            <el-form label-width="100px" inline>
              <el-form-item label="测试模型">
                <div style="display:flex;flex-direction:column;gap:6px">
                  <el-select v-model="testModel" style="width:340px" filterable allow-create default-first-option placeholder="选择模型">
                    <el-option-group v-for="g in modelGroups" :key="g.label" :label="g.label">
                      <el-option v-for="m in g.models" :key="m.value" :label="m.label" :value="m.value" />
                    </el-option-group>
                  </el-select>
                  <el-input v-model="testModel" style="width:340px" placeholder="或手动输入模型 Code" clearable />
                </div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="testing" @click="handleTest">开始测试</el-button>
              </el-form-item>
            </el-form>

            <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'fail'">
              <div class="test-row">
                <el-icon v-if="testResult.success" color="#52c41a"><CircleCheck /></el-icon>
                <el-icon v-else color="#f5222d"><CircleClose /></el-icon>
                <span>{{ testResult.success ? '连接成功' : '连接失败' }}</span>
                <el-tag v-if="testResult.success" type="success" size="small">
                  {{ testResult.latency_ms }} ms
                </el-tag>
              </div>
              <div v-if="testResult.success" style="margin-top:8px;color:#595959;font-size:13px">
                模型响应：{{ testResult.response }}
              </div>
              <div v-else style="margin-top:8px;color:#f5222d;font-size:13px">
                错误：{{ testResult.error }}
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- ── Tab 2：用量统计 ── -->
      <el-tab-pane label="用量统计" name="stats">
        <div class="tab-body">

          <!-- 时间筛选 -->
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
            <span style="font-size:14px;color:#606266">时间范围：</span>
            <el-radio-group v-model="statsDays" @change="loadStats">
              <el-radio-button :value="7">近7天</el-radio-button>
              <el-radio-button :value="30">近30天</el-radio-button>
              <el-radio-button :value="90">近90天</el-radio-button>
            </el-radio-group>
            <el-button :loading="statsLoading" @click="loadStats">刷新</el-button>
          </div>

          <!-- 汇总指标卡 -->
          <el-row :gutter="12" style="margin-bottom:16px">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.totals?.total_calls ?? 0 }}</div>
                <div class="stat-label">总调用次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ (stats.totals?.success_calls ?? 0) }}</div>
                <div class="stat-label">成功次数
                  <span v-if="stats.totals?.total_calls" style="font-size:11px;color:#8c8c8c">
                    （{{ Math.round((stats.totals.success_calls / stats.totals.total_calls) * 100) }}%）
                  </span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ fmtNum(stats.totals?.total_tokens) }}</div>
                <div class="stat-label">总 Token 用量</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ stats.totals?.avg_latency_ms ? Math.round(stats.totals.avg_latency_ms) + ' ms' : '-' }}</div>
                <div class="stat-label">平均响应时间</div>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="12" style="margin-bottom:16px">
            <!-- 按操作类型 -->
            <el-col :span="12">
              <el-card shadow="never">
                <template #header><span class="card-title">按操作类型</span></template>
                <el-table :data="stats.by_operation" size="small">
                  <el-table-column prop="operation_name" label="类型" />
                  <el-table-column prop="calls" label="次数" width="80" />
                  <el-table-column prop="success" label="成功" width="80" />
                  <el-table-column label="Token" width="100">
                    <template #default="{ row }">{{ fmtNum(row.tokens) }}</template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <!-- 按模型 -->
            <el-col :span="12">
              <el-card shadow="never">
                <template #header><span class="card-title">按模型</span></template>
                <el-table :data="stats.by_model" size="small">
                  <el-table-column prop="model" label="模型" />
                  <el-table-column prop="calls" label="次数" width="80" />
                  <el-table-column label="Token" width="100">
                    <template #default="{ row }">{{ fmtNum(row.tokens) }}</template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>

          <!-- 每日趋势 -->
          <el-card shadow="never" style="margin-bottom:16px">
            <template #header><span class="card-title">每日调用趋势</span></template>
            <el-table :data="stats.daily" size="small" max-height="260">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="calls" label="调用次数" width="100" />
              <el-table-column label="Token 用量">
                <template #default="{ row }">
                  {{ fmtNum(row.tokens) }}
                  <el-progress
                    :percentage="maxDailyTokens ? Math.round((row.tokens / maxDailyTokens) * 100) : 0"
                    :show-text="false"
                    style="width:120px;display:inline-block;margin-left:8px;vertical-align:middle"
                  />
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 最近调用记录 -->
          <el-card shadow="never">
            <template #header><span class="card-title">最近调用记录（最多50条）</span></template>
            <el-table :data="stats.recent" size="small" max-height="320" stripe>
              <el-table-column prop="created_at" label="时间" width="160">
                <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
              </el-table-column>
              <el-table-column prop="operation_name" label="操作" width="100" />
              <el-table-column prop="model" label="模型" width="120" />
              <el-table-column label="状态" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                    {{ row.success ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="total_tokens" label="Token" width="80" />
              <el-table-column prop="latency_ms" label="耗时(ms)" width="90" />
              <el-table-column label="错误信息">
                <template #default="{ row }">
                  <span v-if="row.error_msg" style="color:#f5222d;font-size:12px">{{ row.error_msg }}</span>
                  <span v-else style="color:#ccc">-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>

    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { getAIConfig, saveAIConfig, testAIModel, getAIUsageStats } from '../../api/admin'

const activeTab = ref('config')

// ─── 配置 Tab ─────────────────────────────────────────
const configData      = ref({ api_key_masked: '', has_key: false, key_source: 'none', tag_model: 'qwen-plus', gen_model: 'qwen-plus', updated_at: '' })
const availableModels = ref([])
const modelGroups = computed(() => {
  const map = {}
  availableModels.value.forEach(m => {
    const g = m.group || '其他'
    if (!map[g]) map[g] = []
    map[g].push(m)
  })
  return Object.entries(map).map(([label, models]) => ({ label, models }))
})
const hasKey          = computed(() => configData.value.has_key)
const saving          = ref(false)
const editingKey      = ref(false)
const newApiKey       = ref('')

async function loadConfig() {
  try {
    const res = await getAIConfig()
    configData.value      = res
    availableModels.value = res.available_models || []
    testModel.value       = res.tag_model || 'qwen-plus'
  } catch { /* empty */ }
}

function toggleEditKey() {
  if (editingKey.value) {
    editingKey.value = false
    newApiKey.value  = ''
  } else {
    editingKey.value = true
    newApiKey.value  = ''
  }
}

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      tag_model: configData.value.tag_model,
      gen_model: configData.value.gen_model,
    }
    if (editingKey.value && newApiKey.value.trim()) {
      payload.api_key = newApiKey.value.trim()
    }
    await saveAIConfig(payload)
    ElMessage.success('配置已保存')
    editingKey.value = false
    newApiKey.value  = ''
    await loadConfig()
  } finally {
    saving.value = false
  }
}

async function handleClearKey() {
  saving.value = true
  try {
    await saveAIConfig({ tag_model: configData.value.tag_model, gen_model: configData.value.gen_model, api_key: '' })
    ElMessage.success('已清除管理页面设置的 Key，将回退到 .env 文件')
    await loadConfig()
  } finally {
    saving.value = false
  }
}

// ─── 模型测试 ─────────────────────────────────────────
const testModel  = ref('qwen-plus')
const testing    = ref(false)
const testResult = ref(null)

async function handleTest() {
  testing.value    = true
  testResult.value = null
  try {
    const res = await testAIModel(testModel.value)
    testResult.value = res
  } catch {
    testResult.value = { success: false, error: '请求失败，请检查网络或 API Key' }
  } finally {
    testing.value = false
  }
}

// ─── 用量统计 Tab ──────────────────────────────────────
const statsDays   = ref(30)
const statsLoading = ref(false)
const stats       = ref({ totals: {}, by_operation: [], by_model: [], daily: [], recent: [] })

const maxDailyTokens = computed(() => {
  const vals = stats.value.daily.map(d => d.tokens || 0)
  return vals.length ? Math.max(...vals) : 1
})

async function loadStats() {
  statsLoading.value = true
  try {
    const res = await getAIUsageStats(statsDays.value)
    stats.value = res
  } finally {
    statsLoading.value = false
  }
}

function fmtNum(n) {
  if (!n) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000)    return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

function fmtTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

onMounted(() => {
  loadConfig()
  loadStats()
})
</script>

<style scoped>
.tab-body { padding: 8px 0; }

.setting-card {
  margin-bottom: 16px;
}
.card-title {
  font-weight: 600;
  color: #21242C;
}
.field-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

/* 测试结果 */
.test-result {
  margin-top: 12px;
  padding: 12px 16px;
  border-radius: 6px;
  border: 1px solid;
}
.test-result.success {
  border-color: #b7eb8f;
  background: #f6ffed;
}
.test-result.fail {
  border-color: #ffa39e;
  background: #fff1f0;
}
.test-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

/* 统计卡片 */
.stat-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 20px 16px;
  text-align: center;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1865F2;
  line-height: 1.2;
}
.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: #6B7280;
}
</style>
