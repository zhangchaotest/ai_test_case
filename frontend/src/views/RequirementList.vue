<template>
  <div class="view-container">
    <!-- 1. 顶部搜索栏 (仿截图风格) -->
    <el-card shadow="never" class="filter-container">
      <el-form :inline="true" :model="filters" class="demo-form-inline">
        <el-form-item label="需求ID">
          <el-input v-model="filters.id" placeholder="请输入 ID" clearable/>
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="filters.feature" placeholder="模糊搜索" clearable/>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部" clearable style="width: 120px">
            <el-option label="P0" value="P0"/>
            <el-option label="P1" value="P1"/>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 2. 数据表格 -->
    <el-card shadow="never" class="table-container">
      <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
        <el-table-column type="selection" width="55"/>
        <el-table-column prop="id" label="需求ID" width="80" sortable/>
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
            <!-- 6. 点击数量跳转到测试用例页面 -->
            <el-link type="primary" :underline="false" @click="goToCases(row.id)">
              {{ row.case_count }} 条
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <!-- 5. 生成用例按钮 -->
            <el-button type="primary" link @click="openGenerateDrawer(row)">
              <el-icon>
                <MagicStick/>
              </el-icon>
              生成用例
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 4. 翻页 -->
      <div class="pagination-wrapper">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="fetchData"
            @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 5. 右侧弹窗：流式输出展示 (Drawer) -->
    <el-drawer
        v-model="drawerVisible"
        title="🤖 AI 智能生成中..."
        size="40%"
        :close-on-click-modal="false"
    >
      <div class="console-box">
        <div class="console-header">System Console</div>
        <!-- 日志区域 -->
        <div class="console-content" ref="consoleRef">
          <div v-for="(log, index) in logs" :key="index" class="log-line">
            <span class="log-time">[{{ log.time }}]</span>
            <!-- 根据 type 动态改变颜色 -->
            <span :class="['log-msg', log.type]">{{ log.msg }}</span>
          </div>
          <div v-if="isGenerating" class="loading-cursor">_</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="drawerVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToCases(currentReqId)" :disabled="isGenerating">
          查看生成结果
        </el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {Search, Refresh, Download, MagicStick} from '@element-plus/icons-vue'
import {getRequirements, generateCases} from '../api/api.js' // 假设api.js已封装
import {ElMessage} from 'element-plus'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const filters = reactive({
  id: '',
  feature: '',
  priority: ''
})

// Drawer 相关
const drawerVisible = ref(false)
const logs = ref([])
const isGenerating = ref(false)
const currentReqId = ref(null)

// 模拟获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // 实际项目中应该把 filters, page 传给后端
    const res = await getRequirements()
    let data = res.data

    // 前端简单过滤 (如果后端没做分页)
    if (filters.id) data = data.filter(item => String(item.id).includes(filters.id))
    if (filters.feature) data = data.filter(item => item.feature_name.includes(filters.feature))

    total.value = data.length
    tableData.value = data // 这里应该做 slice 分页
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 5. 点击生成用例
const openGenerateDrawer = async (row) => {
  drawerVisible.value = true
  currentReqId.value = row.id
  logs.value = []
  isGenerating.value = true

  addLog(`🚀 系统启动: 开始分析需求 [${row.feature_name}]...`)

  try {
    const response = await fetch(`http://localhost:8000/requirements/${row.id}/generate_stream`)

    if (!response.ok) throw new Error("连接后端失败")

    const reader = response.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buffer = '' // 🔥 增加缓冲区，防止数据被截断

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk

      // 按双换行符分割 SSE 消息块
      const parts = buffer.split('\n\n')
      // 最后一部分可能是不完整的，留给下一次循环处理
      buffer = parts.pop()

      for (const part of parts) {
        parseSSEMessage(part) // 解析完整的消息块
      }
    }

    // 处理剩余的 buffer
    if (buffer.trim()) parseSSEMessage(buffer)
    addLog(`✅ 流程结束: 所有用例已入库！`, 'success')
    await fetchData()

  } catch (e) {
    addLog(`❌ 发生错误: ${e.message}`, 'danger') // danger 会显示红色
  } finally {
    isGenerating.value = false
  }
}

// 解析 SSE 格式的数据 (data: {...})
// 🔥 新的解析函数：专门处理 event 和 data 分离的情况
const parseSSEMessage = (messageString) => {
  const lines = messageString.split('\n')
  let eventType = 'message'
  let dataStr = ''

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.replace('event: ', '').trim()
    } else if (line.startsWith('data: ')) {
      dataStr = line.replace('data: ', '').trim()
    }
  }

  // 1. 如果是结束信号
  if (eventType === 'finish') return

  // 2. 如果有数据，尝试解析 JSON
  if (dataStr) {
    try {
      // 兼容处理：有时候后端传来的 \\n 需要前端还原（JSON.parse通常会自动处理，但为了保险）
      const data = JSON.parse(dataStr)

      if (data.type === 'log') {
         // 内容可能包含 markdown，直接展示
         addLog(`🤖 [${data.source}]:\n${data.content}`)
      } else if (data.type === 'tool_call') {
         addLog(`🛠️ ${data.content}`, 'warning')
      } else if (data.type === 'tool_result') {
         addLog(`💾 ${data.content}`, 'success')
      }
    } catch (e) {
      console.warn('JSON解析忽略:', dataStr)
    }
  }
}

// 稍微优化一下日志样式函数
const addLog = (msg, type = 'info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({time, msg, type})

  // 自动滚动到底部
  setTimeout(() => {
    const box = document.querySelector('.console-content')
    if (box) box.scrollTop = box.scrollHeight
  }, 100)
}

// 6. 跳转到测试用例页面 (带参数)
const goToCases = (reqId) => {
  router.push({path: '/cases', query: {reqId: reqId}})
  drawerVisible.value = false // 如果是从弹窗跳的，关闭弹窗
}

const resetFilters = () => {
  filters.id = ''
  filters.feature = ''
  filters.priority = ''
  fetchData()
}

const handleExport = () => {
  ElMessage.success('正在导出 Excel...')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.view-container {
  background: #fff;
  padding: 0;
  min-height: 100%;
}

.filter-container {
  margin-bottom: 10px;
  border: none;
  border-bottom: 1px solid #eee;
  border-radius: 0;
}

.table-container {
  border: none;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 黑色控制台风格 */
.console-box {
  background: #1e1e1e;
  color: #00ff00;
  border-radius: 4px;
  height: 400px;
  display: flex;
  flex-direction: column;
  font-family: 'Courier New', Courier, monospace;
}

.console-header {
  background: #333;
  color: #fff;
  padding: 5px 10px;
  font-size: 12px;
}

.console-content {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}

.log-line {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.4;
}

.log-time {
  color: #888;
  margin-right: 8px;
}

.loading-cursor {
  display: inline-block;
  animation: blink 1s infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.log-msg {
  white-space: pre-wrap;
  word-break: break-all;
}

.log-msg.info {
  color: #fff;
}

/* 普通思考: 白色 */
.log-msg.warning {
  color: #e6a23c;
}

/* 工具调用: 黄色 */
.log-msg.success {
  color: #67c23a;
}

/* 保存成功: 绿色 */

.console-content {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #333;
}
/* 关键样式：保留空格和换行 */
.log-msg {
  white-space: pre-wrap; /* 🔥 关键：让 \n 能够换行显示 */
  word-break: break-all;
  line-height: 1.5;
  font-family: Consolas, Monaco, monospace; /* 使用等宽字体，显示代码更好看 */
}

.log-msg.warning { color: #e6a23c; }  /* 黄色 */
.log-msg.success { color: #67c23a; }  /* 绿色 */
.log-msg.danger { color: #f56c6c; }   /* 红色 */

.log-line {
  margin-bottom: 8px; /* 增加行间距 */
  border-bottom: 1px dashed #333; /* 增加分隔线方便阅读 */
  padding-bottom: 4px;
}
</style>
