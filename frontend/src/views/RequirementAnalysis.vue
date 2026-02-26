<template>
  <div class="analysis-container">
    <!-- 分栏布局 (左侧输入，右侧日志) -->
    <div class="main-section">

      <!-- 左侧：需求录入面板 -->
      <div class="left-panel">
        <el-card class="input-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="header-title">📝 智能需求分析</span>
              <!-- 文件上传组件 -->
              <el-upload
                action=""
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileUpload"
                accept=".md,.txt"
              >
                <el-tooltip content="支持 .md 或 .txt 文件" placement="top">
                  <el-button type="primary" plain link icon="Document">导入文档</el-button>
                </el-tooltip>
              </el-upload>
            </div>
          </template>

          <div class="card-body">
            <el-alert
              title="⚠️ 注意事项"
              type="warning"
              :closable="false"
              style="margin-bottom: 10px"
            >
              <ul class="alert-list">
                <li>请勿提交隐私数据</li>
                <li>请勿提交非技术类需求</li>
                <li>请勿提交重复需求</li>
              </ul>
            </el-alert>
          </div>

          <el-form :model="form" label-position="top" class="analysis-form">
            <!-- 1. 项目选择 -->
            <el-form-item label="所属项目" required class="inline-item">
              <el-select
                v-model="form.projectId"
                placeholder="请选择或搜索项目"
                style="width:100%"
                filterable
                default-first-option
              >
                <el-option
                  v-for="p in projects"
                  :key="p.id"
                  :label="p.project_name"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>

            <!-- 2. 需求内容输入 -->
            <el-form-item label="原始需求内容" required class="flex-grow-item">
              <el-input
                v-model="form.rawReq"
                type="textarea"
                resize="none"
                placeholder="请直接粘贴需求文本，或者点击右上方导入文档..."
              />
            </el-form-item>

            <!-- 3. 补充指令 -->
            <el-form-item label="补充指令 (可选)">
              <el-input
                v-model="form.instruction"
                placeholder="例如：忽略非功能性需求，重点关注权限控制..."
              />
            </el-form-item>

            <!-- 4. 操作按钮 -->
            <div class="form-actions">
              <el-button
                type="primary"
                size="large"
                :icon="MagicStick"
                :loading="isAnalyzing"
                @click="startAnalysis"
                style="width: 100%"
              >
                {{ isAnalyzing ? '正在智能分析中...' : '开始双智能体分析' }}
              </el-button>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧：控制台日志 -->
      <div class="right-panel">
        <div class="console-box">
          <div class="console-header">
            <span class="console-title">🤖 协作日志 (Analyst -> Reviewer)</span>
            <el-tag v-if="savedCount > 0" type="success" size="small" effect="dark">
              已入库 {{ savedCount }} 条
            </el-tag>
          </div>
          <div class="console-content" ref="consoleRef">
            <div v-if="logs.length === 0" class="empty-log">
              等待任务启动...
            </div>
            <div v-for="(log, idx) in logs" :key="idx" class="log-line">
              <span class="log-time">[{{ log.time }}]</span>
              <span :class="['log-msg', log.type]">{{ log.msg }}</span>
            </div>
            <!-- 光标闪烁动画 -->
            <div v-if="isAnalyzing" class="loading-cursor">_</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { MagicStick, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 🔥 引入统一封装的 API 和 BASE_URL
import { getProjects, BASE_URL } from '../api/api.js'

// --- 状态定义 ---
const projects = ref([])
const isAnalyzing = ref(false)
const savedCount = ref(0)
const logs = ref([])
const consoleRef = ref(null)

defineOptions({
  name: 'RequirementAnalysis'
})

// 表单数据
const form = reactive({
  projectId: null,
  rawReq: '',
  instruction: ''
})

// --- 1. 初始化与项目加载 ---
onMounted(async () => {
  await loadProjects()
})

const loadProjects = async () => {
  try {
    const res = await getProjects()
    projects.value = res.data.items || []
  } catch (e) {
    ElMessage.error('获取项目列表失败')
  }
}

// --- 2. 文件上传与解析 ---
const handleFileUpload = (file) => {
  const isText = file.name.endsWith('.md') || file.name.endsWith('.txt')
  if (!isText) {
    ElMessage.warning('目前仅支持 .md 或 .txt 文件')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    form.rawReq = e.target.result
    ElMessage.success(`文档 [${file.name}] 解析成功`)
  }
  reader.readAsText(file.raw)
}

// --- 3. 启动流式分析 ---
const startAnalysis = async () => {
  if (!form.projectId) return ElMessage.warning('请先选择所属项目')
  if (!form.rawReq) return ElMessage.warning('请输入或导入需求内容')

  isAnalyzing.value = true
  logs.value = []
  savedCount.value = 0

  try {
    const response = await fetch(`${BASE_URL}/analyze/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: form.projectId,
        raw_req: form.rawReq,
        instruction: form.instruction
      })
    })

    if (!response.ok) throw new Error("后端连接失败")

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()

      for (const part of parts) {
        parseSSEMessage(part)
      }
    }

    if (buffer.trim()) parseSSEMessage(buffer)

    addLog('✨ 分析完成！所有功能点已存入数据库。', 'success')

  } catch (e) {
    addLog(`❌ 分析过程中断: ${e.message}`, 'danger')
  } finally {
    isAnalyzing.value = false
  }
}

const parseSSEMessage = (messageString) => {
  const lines = messageString.split('\n')
  let dataStr = ''

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      dataStr = line.replace('data: ', '').trim()
    }
  }

  if (!dataStr) return

  try {
    const data = JSON.parse(dataStr)

    if (data.type === 'log') {
      const isSystem = data.source === '系统' || data.source === 'system'
      addLog(`${data.source}: ${data.content}`, isSystem ? 'system' : 'info')
    }
    else if (data.type === 'tool_call') {
      addLog(`🛠️ ${data.content}`, 'warning')
    }
    else if (data.type === 'tool_result') {
      if (data.content.includes('成功') || data.content.includes('ID:')) {
        savedCount.value++
        addLog(`💾 ${data.content}`, 'success')
      } else {
        addLog(`⚠️ ${data.content}`, 'warning')
      }
    }
  } catch (e) {}
}

const addLog = (msg, type = 'info') => {
  logs.value.push({
    time: new Date().toLocaleTimeString(),
    msg, type
  })

  nextTick(() => {
    if (consoleRef.value) {
      consoleRef.value.scrollTop = consoleRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.analysis-container {
  height: 100%;
  padding: 15px;
  background-color: #f0f2f5;
  box-sizing: border-box;
  overflow: hidden;
}

/* 主体区域：充满整个页面 */
.main-section {
  display: flex;
  height: 100%;
  gap: 15px;
}

.left-panel {
  flex: 4;
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 6;
  display: flex;
  flex-direction: column;
}

/* 卡片样式覆写 */
.input-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-title {
  font-weight: bold;
  font-size: 15px;
  color: #303133;
}

/* 表单布局 */
.analysis-form {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 特殊处理：项目选择行内展示 */
.inline-item {
  margin-bottom: 15px;
}
/* 需求内容自适应填满 */
.flex-grow-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 15px;
  min-height: 0; /* Flex 嵌套关键，防止溢出 */
}
:deep(.flex-grow-item .el-form-item__content) {
  flex: 1;
  height: 100%;
}
:deep(.flex-grow-item .el-textarea) {
  height: 100%;
}
:deep(.flex-grow-item .el-textarea__inner) {
  height: 100% !important;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  resize: none; /* 禁止手动拖动，完全靠 Flex 撑开 */
}
/* 强制 Label 和 Input 并排 */
:deep(.inline-item .el-form-item__label) {
  float: left;
  line-height: 32px;
  margin-right: 12px;
  padding-bottom: 0 !important; /* 抵消 label-position=top 的 padding */
}
:deep(.inline-item .el-form-item__content) {
  line-height: 32px;
}

:deep(.el-form-item__content) {
  flex: 1;
}
:deep(.el-textarea__inner) {
  height: 100% !important;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

/* 控制台样式 */
.console-box {
  background: #1e1e1e;
  color: #e0e0e0;
  border-radius: 4px;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #333;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.console-header {
  background: #2d2d2d;
  padding: 8px 15px;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.console-title {
  font-weight: bold;
  font-size: 13px;
  color: #fff;
}

.console-content {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.empty-log {
  color: #666;
  text-align: center;
  margin-top: 50px;
  font-style: italic;
}

.log-line {
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  word-break: break-all;
}

.log-time {
  color: #666;
  margin-right: 10px;
  min-width: 65px;
  font-size: 12px;
}

.log-msg { white-space: pre-wrap; flex: 1; }
.log-msg.system { color: #c586c0; font-weight: bold; }
.log-msg.info { color: #9cdcfe; }
.log-msg.warning { color: #dcdcaa; }
.log-msg.success { color: #6a9955; font-weight: bold; }
.log-msg.danger { color: #f44747; }

.loading-cursor {
  display: inline-block;
  color: #409eff;
  animation: blink 1s infinite;
  margin-left: 5px;
}
@keyframes blink { 50% { opacity: 0; } }
</style>