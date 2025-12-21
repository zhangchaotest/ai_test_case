<!-- frontend/src/views/RequirementAnalysis.vue -->
<template>
  <div class="analysis-container">
    <!-- 左侧：输入区 -->
    <div class="left-panel">
      <el-card class="input-card" shadow="never">
        <template #header>
          <span class="card-title">📝 需求录入</span>
        </template>

        <el-form :model="form" label-position="top">
          <!-- 1.2 项目关联 -->
          <el-form-item label="所属项目" required>
            <el-select
              v-model="form.projectId"
              placeholder="请选择项目"
              filterable
              allow-create
              default-first-option
              @change="handleProjectChange"
              style="width: 100%"
            >
              <el-option
                v-for="item in projects"
                :key="item.id"
                :label="item.project_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>

          <!-- 1.3 需求上传 -->
          <el-form-item label="原始需求内容" required>
            <el-input
              v-model="form.rawReq"
              type="textarea"
              :rows="12"
              placeholder="请粘贴需求文档内容，或者输入具体的功能描述..."
            />
          </el-form-item>

          <!-- 1.4 补充指令 -->
          <el-form-item label="补充指令 (可选)">
            <el-input
              v-model="form.instruction"
              placeholder="例如：请重点关注权限控制；或者：忽略UI相关的细节"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :icon="MagicStick"
              :loading="isAnalyzing"
              @click="startAnalysis"
              style="width: 100%"
            >
              开始智能分析
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 右侧：输出区 -->
    <div class="right-panel">
      <div class="console-box">
        <div class="console-header">
          <span>🤖 分析结果输出</span>
          <el-tag v-if="savedCount > 0" type="success" size="small">已拆解 {{ savedCount }} 个功能点</el-tag>
        </div>
        <div class="console-content" ref="consoleRef">
          <div v-for="(log, index) in logs" :key="index" class="log-line">
            <span class="log-time">[{{ log.time }}]</span>
            <span :class="['log-msg', log.type]">{{ log.msg }}</span>
          </div>
          <div v-if="isAnalyzing" class="loading-cursor">_</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios' // 直接用 axios 或者你的 api 封装

const projects = ref([])
const isAnalyzing = ref(false)
const savedCount = ref(0)
const logs = ref([])
const consoleRef = ref(null)

const form = reactive({
  projectId: null,
  rawReq: '',
  instruction: ''
})

// 加载项目列表
const loadProjects = async () => {
  try {
    // 假设 api.js 里有 getProjects
    const res = await axios.get('http://localhost:8000/projects')
    projects.value = res.data
  } catch (e) {
    console.error(e)
  }
}

// 处理项目选择（支持新建）
const handleProjectChange = async (val) => {
  if (typeof val === 'string') {
    // 用户输入了新项目名，自动创建
    try {
      const res = await axios.post('http://localhost:8000/projects', { name: val })
      projects.value.push({ id: res.data.id, project_name: res.data.name })
      form.projectId = res.data.id
      ElMessage.success(`项目 [${val}] 创建成功`)
    } catch (e) {
      ElMessage.error('创建项目失败')
    }
  }
}

// 开始分析 (POST 流式)
const startAnalysis = async () => {
  if (!form.projectId || !form.rawReq) {
    ElMessage.warning('请选择项目并输入需求')
    return
  }

  isAnalyzing.value = true
  logs.value = []
  savedCount.value = 0
  addLog('🚀 正在提交分析请求...', 'info')

  try {
    const response = await fetch('http://localhost:8000/analyze/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: form.projectId,
        raw_req: form.rawReq,
        instruction: form.instruction
      })
    })

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
        parseSSE(part)
      }
    }

    addLog('✨ 分析完成！所有功能点已存入数据库。', 'success')

  } catch (e) {
    addLog(`❌ 错误: ${e.message}`, 'danger')
  } finally {
    isAnalyzing.value = false
  }
}

const parseSSE = (msg) => {
  // 复用之前的 SSE 解析逻辑
  const lines = msg.split('\n')
  let dataStr = ''
  for (const line of lines) {
    if (line.startsWith('data: ')) dataStr = line.replace('data: ', '').trim()
  }
  if (!dataStr) return

  try {
    const data = JSON.parse(dataStr)
    if (data.type === 'log') {
      addLog(`${data.source}: ${data.content}`, 'info')
    } else if (data.type === 'tool_call') {
      addLog(`🛠️ ${data.content}`, 'warning')
    } else if (data.type === 'tool_result') {
      if (data.content.includes('成功')) savedCount.value++ // 简单计数
      addLog(`💾 ${data.content}`, 'success')
    }
  } catch(e) {}
}

const addLog = (msg, type='info') => {
  logs.value.push({
    time: new Date().toLocaleTimeString(),
    msg, type
  })
  setTimeout(() => {
    if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
  }, 100)
}

onMounted(() => loadProjects())
</script>

<style scoped>
.analysis-container {
  display: flex;
  height: calc(100vh - 84px); /* 减去 Header 高度 */
  gap: 20px;
  padding: 20px;
  background: #f0f2f5;
}

.left-panel { flex: 1; display: flex; flex-direction: column; }
.right-panel { flex: 1; display: flex; flex-direction: column; }

.input-card { flex: 1; display: flex; flex-direction: column; }
/* 让输入框撑满 */
:deep(.el-card__body) { height: 100%; display: flex; flex-direction: column; }
:deep(.el-form) { flex: 1; display: flex; flex-direction: column; }
:deep(.el-textarea__inner) { height: 100% !important; resize: none; }

/* 复用之前的 Console 样式 */
.console-box {
  background: #1e1e1e; color: #e0e0e0;
  border-radius: 8px; flex: 1;
  display: flex; flex-direction: column;
  font-family: 'Consolas', monospace;
  border: 1px solid #333;
}
.console-header {
  background: #2d2d2d; color: #fff; padding: 10px 15px;
  border-bottom: 1px solid #444; font-weight: bold;
  display: flex; justify-content: space-between; align-items: center;
}
.console-content { padding: 15px; overflow-y: auto; flex: 1; }
.log-line { margin-bottom: 8px; line-height: 1.5; font-size: 13px; display: flex; }
.log-time { color: #666; margin-right: 10px; min-width: 65px; }
.log-msg { white-space: pre-wrap; word-break: break-all; }
.log-msg.info { color: #a6e22e; }
.log-msg.warning { color: #e6a23c; }
.log-msg.success { color: #67c23a; }
.log-msg.danger { color: #f56c6c; }
</style>