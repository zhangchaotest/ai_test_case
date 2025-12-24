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
        <el-button
            type="success"
            :icon="Check"
            plain
            :disabled="selectedIds.length === 0"
            @click="handleBatchReview('Active')"
        >
          批量通过
        </el-button>
        <el-button
            type="danger"
            :icon="Close"
            plain
            :disabled="selectedIds.length === 0"
            @click="handleBatchReview('Deprecated')"
        >
          批量废弃
        </el-button>
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
import {Check, Close} from '@element-plus/icons-vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import ProTable from '../components/ProTable.vue'
import {getAllTestCases, batchUpdateCaseStatus} from '../api/api.js' // 确保这里引入了批量接口

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