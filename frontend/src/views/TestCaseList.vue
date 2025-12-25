<template>
  <div class="view-container">
    <pro-table
        ref="proTableRef"
        :api="getAllTestCases"
        :init-param="initSearchParams"
        @selection-change="handleSelectionChange"
    >
      <!-- ================== 1. 搜索区域插槽 ================== -->
      <template #search="{ params }">
        <el-form-item label="需求ID">
          <!-- 后端参数名是 req_id -->
          <el-input v-model="params.req_id" placeholder="精确匹配" clearable style="width: 150px"/>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="params.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="草稿" value="Draft"/>
            <el-option label="有效" value="Active"/>
            <el-option label="废弃" value="Deprecated"/>
          </el-select>
        </el-form-item>

        <el-form-item label="用例标题">
          <el-input v-model="params.title" placeholder="模糊搜索" clearable/>
        </el-form-item>
      </template>

      <!-- ================== 2. 工具栏插槽 (批量按钮) ================== -->
      <template #toolbar>
        <el-button type="success" :icon="Check" plain :disabled="selectedIds.length === 0" @click="handleBatchReview('Active')">批量通过</el-button>
        <el-button type="danger" :icon="Close" plain :disabled="selectedIds.length === 0" @click="handleBatchReview('Deprecated')">批量废弃</el-button>
               <!-- 🔥 新增：导出按钮组 -->
        <el-dropdown style="margin-left: 10px" @command="handleExport">
          <el-button type="primary" :icon="Download" plain>
            导出用例 <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">导出 Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="csv">导出 CSV (.csv)</el-dropdown-item>
              <el-dropdown-item command="markdown">导出 Markdown (推荐XMind导入)</el-dropdown-item>
              <el-dropdown-item command="xmind">导出 XMind (.xmind)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>

      <!-- ================== 3. 表格列定义 (默认插槽) ================== -->

      <!-- 多选框 (必选，否则无法批量) -->
      <el-table-column type="selection" width="55"/>

      <el-table-column prop="id" label="ID" width="80"/>

      <el-table-column prop="requirement_id" label="需求ID" width="100">
        <template #default="{ row }">
          <el-link type="primary" @click="goToRequirement(row.requirement_id)">
            #{{ row.requirement_id }}
          </el-link>
        </template>
      </el-table-column>

      <el-table-column prop="case_title" label="用例标题" show-overflow-tooltip/>

      <!-- 详情展开行 -->
      <el-table-column type="expand" label="详情" width="60">
        <template #default="{ row }">
          <div style="padding: 10px 50px; background: #fafafa; border-radius: 4px;">
            <p><strong>前置条件：</strong>{{ row.pre_condition || '无' }}</p>
            <el-table :data="row.steps" border size="small" :key="row.id" style="margin: 10px 0">
              <el-table-column prop="step_id" label="#" width="50"/>
              <el-table-column prop="action" label="步骤操作"/>
              <el-table-column prop="expected" label="预期结果"/>
            </el-table>
            <p v-if="row.test_data && Object.keys(row.test_data).length">
              <strong>测试数据：</strong>{{ row.test_data }}
            </p>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="quality_score" label="质量评分" width="120" align="center" sortable>
        <template #default="{ row }">
          <!-- 悬浮显示评语 -->
          <el-tooltip
              :content="row.review_comments || '无评审意见'"
              placement="top"
              :disabled="!row.review_comments"
          >
            <div style="display: flex; align-items: center; justify-content: center;">
              <!-- 使用环形进度条或条形进度条 -->
              <el-progress
                  type="dashboard"
                  :percentage="Math.round((row.quality_score || 0) * 100)"
                  :width="40"
                  :stroke-width="4"
                  :color="getScoreColor"
              >
                <template #default="{ percentage }">
                  <span style="font-size: 12px; font-weight: bold">{{ percentage }}</span>
                </template>
              </el-progress>
            </div>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="getPriorityTag(row.priority)" effect="dark">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="case_type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getCaseTypeTag(row.case_type)" effect="plain">{{ row.case_type }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-badge is-dot :type="getStatusBadgeType(row.status)" class="status-dot"/>
          {{ getStatusText(row.status) }}
        </template>
      </el-table-column>

    </pro-table>
  </div>
</template>

<script setup>
import {reactive, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Check, Close,Download,ArrowDown} from '@element-plus/icons-vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import ProTable from '../components/ProTable.vue'
import {getAllTestCases, batchUpdateCaseStatus,exportTestCases} from '../api/api.js' // 确保这里引入了批量接口

const route = useRoute()
const router = useRouter()
const proTableRef = ref(null)

// 选中项 ID 集合
const selectedIds = ref([])

defineOptions({
  name: 'TestCaseList'
})

// 初始参数 (从路由获取 reqId)
const initSearchParams = reactive({
  req_id: route.query.reqId || '',
  title: ''
})

// -----------------------------------------
// 核心逻辑 1：处理多选
// -----------------------------------------
// 因为 ProTable 用 v-bind="$attrs" 透传了事件，这里直接接收 el-table 的 selection-change
const handleSelectionChange = (val) => {
  selectedIds.value = val.map(item => item.id)
}

// -----------------------------------------
// 核心逻辑 2：批量评审
// -----------------------------------------
const handleBatchReview = async (newStatus) => {
  const actionText = newStatus === 'Active' ? '通过' : '废弃'

  try {
    await ElMessageBox.confirm(
        `确定要将选中的 ${selectedIds.value.length} 条用例标记为【${actionText}】吗？`,
        '批量评审确认',
        {
          type: 'warning',
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        }
    )

    // 调用后端接口
    await batchUpdateCaseStatus({
      ids: selectedIds.value,
      status: newStatus
    })

    ElMessage.success('操作成功')

    // 刷新表格 (ProTable 暴露的方法)
    proTableRef.value?.refresh()
    // 清空选中 (需要手动置空 selectedIds，表格 UI 的清空通常随 refresh 自动重置，或者调用 clearSelection)
    selectedIds.value = []

  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败: ' + (e.message || e))
    }
  }
}

// -----------------------------------------
// 辅助函数
// -----------------------------------------
const goToRequirement = (reqId) => {
  router.push({path: '/requirements', query: {id: reqId}})
}

const getPriorityTag = (p) => {
  const map = {'P0': 'danger', 'P1': 'warning'}
  return map[p] || 'success'
}

const getCaseTypeTag = (type) => {
  const map = {'Negative': 'danger', 'Boundary': 'warning', 'Performance': 'info'}
  return map[type] || 'primary'
}

// 状态显示辅助
const getStatusBadgeType = (status) => {
  if (status === 'Active') return 'success'
  if (status === 'Deprecated') return 'info'
  return 'warning' // Draft
}

const getStatusText = (status) => {
  const map = {'Active': '有效', 'Deprecated': '废弃', 'Draft': '草稿'}
  return map[status] || status
}
// 动态颜色：高分绿色，低分红色
const getScoreColor = (percentage) => {
  if (percentage >= 90) return '#67c23a'
  if (percentage >= 80) return '#409eff'
  if (percentage >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 处理导出
const handleExport = async (format) => {
  try {
    ElMessage.info(`正在导出 ${format} 文件，请稍候...`)

    // 组装参数 (复用搜索条件)
    const params = {
      format: format,
      req_id: initSearchParams.req_id || undefined, // 使用当前页面的搜索条件
      status: initSearchParams.status || undefined
    }

    const res = await exportTestCases(params)

    // --- 通用下载逻辑 ---
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 根据格式定后缀
    const extMap = { excel: 'xlsx', csv: 'csv', xmind: 'xmind',markdown: 'md' }
    link.download = `测试用例导出_${new Date().getTime()}.${extMap[format]}`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  }
}
</script>

<style scoped>
.view-container {
  background: #fff;
  padding: 20px;
}

.status-dot {
  margin-right: 5px;
  vertical-align: middle;
}
</style>