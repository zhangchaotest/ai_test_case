<template>
  <div class="view-container">
    <el-card shadow="never" class="filter-container">
      <el-alert title="这里只展示评审通过（有效）的测试用例，供测试人员执行测试。" type="info" show-icon :closable="false" style="margin-bottom:10px"/>
      <el-form :inline="true" :model="filters">
        <el-form-item label="需求ID">
          <el-input v-model="filters.reqId" placeholder="需求ID" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">查询待执行用例</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="case_title" label="用例标题" />
        <el-table-column prop="priority" label="级别" width="80">
           <template #default="{ row }">
             <el-tag effect="plain">{{ row.priority }}</el-tag>
           </template>
        </el-table-column>

        <!-- 执行操作 -->
        <el-table-column label="执行结果" width="220" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="success" size="small" @click="markResult(row, 'Pass')">通过</el-button>
              <el-button type="danger" size="small" @click="markResult(row, 'Fail')">失败</el-button>
              <el-button type="warning" size="small" @click="markResult(row, 'Block')">阻塞</el-button>
            </el-button-group>
          </template>
        </el-table-column>

        <!-- 详情展开 (复用之前的) -->
        <el-table-column type="expand" label="详情" width="60">
          <template #default="{ row }">
            <div style="padding: 10px 20px; background: #f9f9f9">
               <p><strong>前置：</strong>{{row.pre_condition}}</p>
               <p><strong>预期：</strong>{{row.expected_result}}</p>
               <el-table :data="row.steps" border size="small">
                 <el-table-column prop="step_id" label="#" width="50" />
                 <el-table-column prop="action" label="步骤" />
                 <el-table-column prop="expected" label="预期" />
               </el-table>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getAllTestCases } from '../api/api.js'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const filters = reactive({ reqId: '' })

defineOptions({
  name: 'TestExecution'
})

const fetchData = async () => {
  loading.value = true
  try {
    // 🔥🔥🔥 核心：强制 status='Active'
    const params = {
      page: 1,
      size: 50,
      req_id: filters.reqId || undefined,
      status: 'Active'
    }
    const res = await getAllTestCases(params)
    tableData.value = res.data.items
  } finally {
    loading.value = false
  }
}

const markResult = (row, result) => {
  // 这里暂时只做前端提示，后续可接 API
  ElMessage.success(`用例 [${row.id}] 执行结果：${result}`)
}

onMounted(() => fetchData())
</script>