<template>
  <div class="view-container">
    <pro-table
      ref="proTableRef"
      :api="getAllTestCases"
      :init-param="initSearchParams"
    >
      <!-- 1. 自定义搜索区域 -->
      <template #search="{ params }">
        <el-form-item label="需求ID">
          <el-input v-model="params.req_id" placeholder="精确匹配" clearable />
        </el-form-item>
        <el-form-item label="用例标题">
          <el-input v-model="params.title" placeholder="模糊搜索" clearable />
        </el-form-item>
      </template>

      <!-- 2. 表格列定义 -->
      <el-table-column type="selection" width="55" />



      <el-table-column prop="id" label="ID" width="80" />

      <el-table-column prop="requirement_id" label="需求ID" width="100">
        <template #default="{ row }">
           <el-link type="primary" @click="goToRequirement(row.requirement_id)">
             #{{ row.requirement_id }}
           </el-link>
        </template>
      </el-table-column>

      <el-table-column prop="case_title" label="用例标题" show-overflow-tooltip />
            <!-- 展开行：显示步骤详情 -->
      <el-table-column type="expand" label="详情" width="60">
        <template #default="{ row }">
          <div style="padding: 10px 50px; background: #fafafa; border-radius: 4px;">
            <p><strong>前置条件：</strong>{{ row.pre_condition || '无' }}</p>
            <el-table :data="row.steps" border size="small" style="margin: 10px 0">
              <el-table-column prop="step_id" label="#" width="50" />
              <el-table-column prop="action" label="步骤操作" />
              <el-table-column prop="expected" label="预期结果" />
            </el-table>
            <p v-if="row.test_data"><strong>测试数据：</strong>{{ row.test_data }}</p>
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
          <el-badge is-dot :type="row.status === 'Active' ? 'success' : 'info'" class="status-dot" />
          {{ row.status }}
        </template>
      </el-table-column>
    </pro-table>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAllTestCases } from '../api/api.js'
import ProTable from '../components/ProTable.vue'

const route = useRoute()
const router = useRouter()

// 🔥 核心：接收路由参数作为初始搜索条件
// 注意：后端接受的参数名是 req_id (下划线)，所以这里 key 要写 req_id
const initSearchParams = reactive({
  req_id: route.query.reqId || '',
  title: ''
})

const goToRequirement = (reqId) => {
  router.push({ path: '/requirements', query: { id: reqId } })
}

// 标签颜色辅助函数
const getPriorityTag = (p) => {
  if (p === 'P0') return 'danger'
  if (p === 'P1') return 'warning'
  return 'success'
}

const getCaseTypeTag = (type) => {
  const map = {
    'Negative': 'danger',
    'Boundary': 'warning',
    'Functional': 'primary',
    'Performance': 'info'
  }
  return map[type] || 'primary'
}
</script>

<style scoped>
.view-container { background: #fff; padding: 20px; }
.status-dot { margin-right: 5px; vertical-align: middle; }
</style>