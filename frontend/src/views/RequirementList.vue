<template>
  <div class="view-container">
    <!--
      1. 使用 ProTable 组件
      - ref="proTableRef": 用于调用 refresh() 方法
      - :api="getRequirements": 传入 API 函数
      - :init-param: 初始搜索参数
    -->
    <pro-table
        ref="proTableRef"
        :api="getRequirements"
        :init-param="{ feature: '', priority: '' }"
    >
      <!-- Slot: 自定义搜索区域 -->
      <template #search="{ params }">
        <el-form-item label="需求ID">
          <el-input v-model="params.id" placeholder="ID" clearable style="width: 100px"/>
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="params.feature" placeholder="模糊搜索" clearable/>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="params.priority" placeholder="全部" clearable style="width: 120px">
            <el-option label="P0" value="P0"/>
            <el-option label="P1" value="P1"/>
          </el-select>
        </el-form-item>
      </template>

      <!-- Slot: 自定义按钮区域 -->
      <template #buttons>
        <el-button type="success" :icon="Download" @click="handleExport">导出Excel</el-button>
      </template>

      <!-- Slot: 表格列定义 -->
      <el-table-column type="selection" width="55"/>
      <el-table-column prop="id" label="ID" width="80" sortable/>
      <el-table-column prop="module_name" label="所属模块" width="120"/>
      <el-table-column prop="feature_name" label="功能名称" width="200" show-overflow-tooltip/>
      <el-table-column prop="description" label="功能描述" show-overflow-tooltip/>

      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="row.priority === 'P0' ? 'danger' : 'warning'">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="关联用例" width="120" align="center">
        <template #default="{ row }">
          <!-- 点击跳转到用例列表 -->
          <el-link type="primary" :underline="false" @click="goToCases(row.id)">
            {{ row.case_count }} 条
          </el-link>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openGenerateDrawer(row)">
            <el-icon>
              <MagicStick/>
            </el-icon>
            生成用例
          </el-button>
        </template>
      </el-table-column>
    </pro-table>

    <!--
      2. AI 流式生成抽屉
    -->
    <el-drawer
        v-model="drawerVisible"
        title="🤖 AI 智能生成中..."
        size="45%"
        :close-on-click-modal="false"
        destroy-on-close
    >
      <div class="drawer-body">
        <!-- 配置区：允许用户调整生成数量 -->
        <div class="config-panel">
          <div class="config-item">
            <span class="label">🎯 目标数量：</span>
            <el-input-number v-model="targetCount" :min="1" :max="20" size="small"/>
          </div>

          <!-- 🔥 新增：增量模式开关 -->
          <div class="config-item" style="margin-left: 20px;">
            <span class="label">模式：</span>
            <el-switch
                v-model="isAppendMode"
                active-text="增量补充"
                inactive-text="覆盖/新建"
                inline-prompt
                style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
                :disabled="isGenerating"
            />
            <!-- 提示信息 -->
            <el-tooltip content="开启后，AI 将读取已有用例，避免重复生成" placement="top">
              <el-icon style="margin-left: 5px; cursor: pointer; color: #909399">
                <QuestionFilled/>
              </el-icon>
            </el-tooltip>
          </div>

          <div class="config-item" style="margin-left: auto;">
            <el-button type="primary" size="small" @click="startGenerate" :loading="isGenerating">
              {{ isGenerating ? '生成中...' : '开始生成' }}
            </el-button>
          </div>
        </div>

        <!-- 控制台区域 -->
        <div class="console-box">
          <div class="console-header">
            <span>System Console</span>
            <span v-if="isGenerating" style="float: right; color: #e6a23c">
               <el-icon class="is-loading"><Loading/></el-icon> Processing...
             </span>
            <span v-else style="float: right; color: #67c23a">Ready</span>
          </div>

          <div class="console-content" ref="consoleRef">
            <div v-for="(log, index) in logs" :key="index" class="log-line">
              <span class="log-time">[{{ log.time }}]</span>
              <!-- 动态绑定 class 实现颜色变化 -->
              <span :class="['log-msg', log.type]">{{ log.msg }}</span>
            </div>
            <!-- 光标动画 -->
            <div v-if="isGenerating" class="loading-cursor">_</div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="drawerVisible = false" :disabled="isGenerating">关闭</el-button>
        <el-button type="primary" @click="goToCases(currentReqId)" :disabled="isGenerating">
          查看结果
        </el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {Download, MagicStick, Loading} from '@element-plus/icons-vue'
import {getRequirements} from '../api/api.js'
import ProTable from '../components/ProTable.vue'
import {ElMessage} from 'element-plus'
import {QuestionFilled} from '@element-plus/icons-vue' // 记得引入图标

const router = useRouter()
const proTableRef = ref(null)

// === 状态定义 ===
const drawerVisible = ref(false)
const logs = ref([])
const isGenerating = ref(false)
const currentReqId = ref(null)
const targetCount = ref(5) // 默认生成 5 条
const consoleRef = ref(null)

// 用例生成模式new新增，append追加
const isAppendMode = ref(true)

// 导出
const handleExport = () => {
  ElMessage.success('正在导出 Excel...')
}

// 跳转到用例列表
const goToCases = (reqId) => {
  console.log('跳转到用例列表', reqId)
  router.push({path: '/cases', query: {reqId: reqId}})
  drawerVisible.value = false
}

// === 日志辅助函数 ===
const addLog = (msg, type = 'info') => {
  const time = new Date().toLocaleTimeString('en-US', {hour12: false})
  logs.value.push({time, msg, type})

  // 自动滚动到底部
  setTimeout(() => {
    if (consoleRef.value) {
      consoleRef.value.scrollTop = consoleRef.value.scrollHeight
    }
  }, 50)
}


// === 新增/修改的状态变量 ===
const currentRow = ref({})      // 暂存当前选中的行数据

// === 1. 打开抽屉（只做初始化，不写业务逻辑） ===
const openGenerateDrawer = (row) => {
  drawerVisible.value = true
  currentRow.value = row // 保存当前行，方便 startGenerate 读取
  logs.value = []
  currentReqId.value = row.id

  // 🔥 智能判断逻辑
  if (row.case_count > 0) {
    // 如果已经有用例，默认开启增量模式，且数量设少一点
    isAppendMode.value = true
    targetCount.value = 3
    addLog(`ℹ️ 检测到该需求已有 ${row.case_count} 条用例，已自动切换为【增量补充模式】`, 'warning')
  } else {
    // 如果是新需求，默认全量模式
    isAppendMode.value = false
    targetCount.value = 5
  }
  // 自动开始生成 (如果不想要自动开始，把这行删掉，让用户点按钮)
  startGenerate()
}

// === 2. 执行生成（核心逻辑封装在这里） ===
const startGenerate = async () => {
  // 从 currentRow 取值，防止变量丢失
  const row = currentRow.value
  if (!row || !row.id) return

  isGenerating.value = true

  // 如果是重新点击开始，建议清空之前的日志，或者加个分割线
  if (logs.value.length > 1) {
    addLog('------------------------------------------------', 'info')
    addLog('🔄 重新启动生成任务...', 'info')
  } else if (logs.value.length === 0) {
    addLog(`🚀 系统启动: 开始分析需求 [${row.feature_name}]...`)
  }

  const modeText = isAppendMode.value ? '增量补充 (Append)' : '全量覆盖 (New)'
  addLog(`⚙️ 配置: 目标数量 ${targetCount.value} 条 | 模式: ${modeText}`)

  try {
    // 🔥 拼接 URL：带上 count 和 mode
    // mode 参数需要后端支持 (根据之前的后端代码改造)
    const modeParam = isAppendMode.value ? 'append' : 'new'
    const url = `http://localhost:8000/requirements/${row.id}/generate_stream?count=${targetCount.value}&mode=${modeParam}`

    const response = await fetch(url)

    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`)

    // 准备读取流
    const reader = response.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buffer = ''

    // 循环读取
    while (true) {
      const {done, value} = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, {stream: true})
      buffer += chunk

      const parts = buffer.split('\n\n')
      buffer = parts.pop()

      for (const part of parts) {
        parseSSEMessage(part)
      }
    }

    if (buffer.trim()) parseSSEMessage(buffer)

    // 刷新表格
    if (proTableRef.value) {
      proTableRef.value.refresh()
    }

  } catch (e) {
    addLog(`❌ 网络或系统错误: ${e.message}`, 'danger')
  } finally {
    isGenerating.value = false
  }
}

// === SSE 消息解析器 ===
const parseSSEMessage = (messageString) => {
  const lines = messageString.split('\n')
  let eventType = 'message'
  let dataStr = ''

  // 提取 event 和 data
  for (const line of lines) {
    if (line.startsWith('event: ')) eventType = line.replace('event: ', '').trim()
    else if (line.startsWith('data: ')) dataStr = line.replace('data: ', '').trim()
  }

  // 1. 处理结束事件 (包含统计数据)
  if (eventType === 'finish') {
    try {
      const stats = JSON.parse(dataStr)
      addLog('✨ ============================', 'info')
      addLog(`📊 任务完成报告：`, 'success')
      addLog(`   - 设计用例: ${stats.generated} 条`, 'success')
      addLog(`   - 成功入库: ${stats.saved} 条`, 'success')
    } catch (e) {
      addLog('✅ 流程结束。', 'success')
    }
    return
  }

  // 2. 处理普通消息
  if (dataStr) {
    try {
      const data = JSON.parse(dataStr)

      if (data.type === 'log') {
        // 过滤掉无意义的思考文本
        if (data.content === '正在思考...') return
        addLog(`${data.source}: ${data.content}`, 'info')
      } else if (data.type === 'tool_call') {
        addLog(`🛠️ ${data.content}`, 'warning')
      } else if (data.type === 'tool_result') {
        // 根据内容判断颜色
        if (data.content.includes('成功') || data.content.includes('✅')) {
          addLog(`✅ ${data.content}`, 'success')
        } else {
          addLog(`⚠️ ${data.content}`, 'warning')
        }
      }
    } catch (e) {
      // 忽略非 JSON 数据
    }
  }
}
</script>

<style scoped>
.view-container {
  background: #fff;
  padding: 20px;
}

/* 抽屉内部布局 */
.drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.config-panel {
  padding: 0 0 15px 0;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
  margin-bottom: 15px;
}

.config-panel .label {
  font-weight: bold;
  font-size: 14px;
  color: #606266;
  margin-right: 10px;
}

/* 黑色控制台风格 */
.console-box {
  background: #1e1e1e;
  color: #e0e0e0;
  border-radius: 8px;
  flex: 1; /* 自动撑满剩余高度 */
  display: flex;
  flex-direction: column;
  font-family: 'Consolas', 'Monaco', monospace;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid #333;
  overflow: hidden; /* 防止圆角溢出 */
}

.console-header {
  background: #2d2d2d;
  padding: 10px 15px;
  border-bottom: 1px solid #444;
  font-size: 13px;
  font-weight: bold;
  letter-spacing: 1px;
  color: #fff;
}

.console-content {
  padding: 15px;
  overflow-y: auto;
  flex: 1;
  background: #1e1e1e;
}

/* 日志行 */
.log-line {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  border-bottom: 1px dashed #333;
  padding-bottom: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.log-time {
  color: #666;
  margin-right: 12px;
  font-size: 12px;
  min-width: 65px;
  user-select: none;
}

.log-msg {
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
}

/* 颜色定义 */
.log-msg.info {
  color: #a6e22e;
}

/* 绿色偏黄 (Monokai Green) */
.log-msg.warning {
  color: #f1c40f;
  font-style: italic;
}

/* 黄色 */
.log-msg.success {
  color: #2ecc71;
  font-weight: bold;
}

/* 纯绿 */
.log-msg.danger {
  color: #f56c6c;
}

/* 红色 */

/* 光标动画 */
.loading-cursor {
  display: inline-block;
  margin-left: 5px;
  color: #409eff;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.config-panel {
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* 防止小屏幕换行 */
}

.config-item {
  display: flex;
  align-items: center;
  margin-right: 15px;
}

.config-panel {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.config-item {
  display: flex;
  align-items: center;
}

.label {
  font-weight: bold;
  font-size: 14px;
  color: #606266;
  margin-right: 8px;
}
</style>