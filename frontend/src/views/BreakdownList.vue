<template>
  <div class="view-container">
    <pro-table
      ref="tableRef"
      :api="getBreakdownList"
      :init-param="initParams"
    >
      <!-- 搜索栏 -->
      <template #search="{ params }">
        <el-form-item label="所属项目">
          <el-select v-model="params.project_id" placeholder="全部项目" clearable filterable>
            <el-option v-for="p in projects" :key="p.id" :label="p.project_name" :value="p.id"/>
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="params.status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="待审核" value="Pending" />
            <el-option label="已通过" value="Pass" />
            <el-option label="已拒绝" value="Reject" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="params.feature_name" placeholder="模糊搜索" clearable />
        </el-form-item>
      </template>

      <!-- 表格列 -->
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="module_name" label="模块" width="100" />
      <el-table-column prop="feature_name" label="功能名称" width="180" show-overflow-tooltip />
      <el-table-column prop="description" label="功能描述" show-overflow-tooltip />
      <el-table-column prop="acceptance_criteria" label="验收标准" show-overflow-tooltip />

      <el-table-column prop="confidence_score" label="AI评分" width="80" align="center">
        <template #default="{ row }">
          <span :style="{ color: row.confidence_score < 0.6 ? 'red' : 'green' }">
            {{ row.confidence_score }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="review_status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.review_status)">
            {{ getStatusText(row.review_status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="220" fixed="right" align="center">
        <template #default="{ row }">
          <!-- 只有非通过状态可以操作 -->
          <div v-if="row.review_status !== 'Pass'">
            <el-button link type="success" @click="handleStatus(row, 'Pass')">通过</el-button>
            <el-button link type="warning" @click="handleStatus(row, 'Reject')" v-if="row.review_status !== 'Reject'">拒绝</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleStatus(row, 'Discard')">废弃</el-button>
          </div>
          <span v-else style="color: #67c23a; font-size: 12px;">已同步至功能点</span>
        </template>
      </el-table-column>
    </pro-table>

    <!-- 编辑弹窗 (复用) -->
    <el-dialog v-model="editVisible" title="编辑并重审" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="所属模块">
          <el-input v-model="editForm.module_name" />
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="editForm.feature_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="验收标准">
          <el-input v-model="editForm.acceptance_criteria" type="textarea" :rows="4"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存并重置为待审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import ProTable from '../components/ProTable.vue'
import { getBreakdownList, updateBreakdownItem, updateBreakdownStatus, getProjects } from '../api/api.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableRef = ref(null)
const projects = ref([])
const initParams = reactive({})

const editVisible = ref(false)
const editForm = reactive({})

// 加载项目用于筛选
onMounted(async () => {
  const res = await getProjects()
  projects.value = res.data
})

// 状态操作
const handleStatus = async (row, status) => {
  const actionMap = { 'Pass': '通过并同步', 'Reject': '拒绝', 'Discard': '废弃(隐藏)' }

  try {
    await ElMessageBox.confirm(
      `确定要【${actionMap[status]}】该条目吗？`,
      '状态变更',
      { type: status === 'Discard' ? 'error' : 'warning' }
    )

    await updateBreakdownStatus(row.id, status)
    ElMessage.success('操作成功')
    tableRef.value?.refresh()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

// 编辑操作
const openEdit = (row) => {
  Object.assign(editForm, row)
  editVisible.value = true
}

const submitEdit = async () => {
  try {
    await updateBreakdownItem(editForm.id, editForm)
    ElMessage.success('修改成功，状态已重置为待审核')
    editVisible.value = false
    tableRef.value?.refresh()
  } catch (e) {
    ElMessage.error('修改失败')
  }
}

// 辅助函数
const getStatusType = (s) => {
  const map = { 'Pending': 'warning', 'Pass': 'success', 'Reject': 'danger' }
  return map[s] || 'info'
}
const getStatusText = (s) => {
  const map = { 'Pending': '待审核', 'Pass': '已通过', 'Reject': '已拒绝' }
  return map[s] || s
}
</script>

<style scoped>
.view-container { background: #fff; padding: 20px; }
</style>

