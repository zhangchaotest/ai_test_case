<template>
  <div class="view-container">
    <el-card shadow="never" class="filter-container">
      <el-form :inline="true" :model="filters">
        <el-form-item label="需求ID">
          <!-- 默认可能会带入 query 参数 -->
          <el-input v-model="filters.reqId" placeholder="关联需求ID" clearable/>
        </el-form-item>
        <el-form-item label="用例标题">
          <el-input v-model="filters.title" placeholder="模糊搜索" clearable/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="success" :icon="Download">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-container">
      <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
        <el-table-column type="selection" width="55"/>
        <el-table-column prop="id" label="用例ID" width="80"/>
        <el-table-column prop="requirement_id" label="关联需求ID" width="100">
          <template #default="{ row }">
            <!-- 7. 点击需求ID跳转回需求页面 -->
            <el-link type="primary" @click="goToRequirement(row.requirement_id)">
              #{{ row.requirement_id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="case_title" label="用例标题" show-overflow-tooltip/>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" effect="dark">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="case_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getCaseTypeTag(row.case_type)" effect="plain">
              {{ row.case_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-badge is-dot :type="row.status === 'Active' ? 'success' : 'info'" class="status-dot"/>
            {{ row.status }}
          </template>
        </el-table-column>

        <!-- 展开行显示步骤 -->
        <el-table-column type="expand" label="详情" width="60">
          <template #default="{ row }">
            <div style="padding: 10px 50px; background: #fafafa;">
              <p><strong>前置条件：</strong>{{ row.pre_condition }}</p>
              <el-table :data="row.steps" border size="small">
                <el-table-column prop="step_id" label="#" width="50"/>
                <el-table-column prop="action" label="步骤操作"/>
                <el-table-column prop="expected" label="预期结果"/>
              </el-table>
              <p style="margin-top:10px"><strong>测试数据：</strong>{{ row.test_data }}</p>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, watch} from 'vue' // 引入依赖
import {useRoute, useRouter} from 'vue-router'
import {Search, Refresh, Download} from '@element-plus/icons-vue'
import {getAllTestCases} from '../api/api.js' // 确保引入了 API

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 1. 先定义响应式数据
const filters = reactive({
  reqId: '',
  title: ''
})

// 2. 再定义 fetchData 函数 (必须在 watch 之前！)
const fetchData = async () => {
  loading.value = true
  try {
    const params = {}

    // 处理参数转换 (驼峰转下划线)
    if (filters.reqId) params.req_id = filters.reqId
    if (filters.title) params.title = filters.title

    const res = await getAllTestCases(params)
    tableData.value = res.data
    total.value = res.data.length
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 3. 最后再写 watch 和 onMounted
// 这样执行的时候，fetchData 已经存在了
watch(() => route.query.reqId, (newId) => {
  if (newId) {
    filters.reqId = newId
    // 此时 fetchData 已经定义过了，可以安全调用
    fetchData()
  } else {
    // 如果没有 ID，也可以选择加载全部，或者清空
    fetchData()
  }
}, {immediate: true}) // immediate: true 会立即触发一次

const goToRequirement = (reqId) => {
  router.push({path: '/requirements', query: {id: reqId}})
}

const resetFilters = () => {
  filters.reqId = ''
  filters.title = ''
  router.replace({query: {}})
  fetchData()
}

const getPriorityType = (p) => {
  if (p === 'P0') return 'danger'
  if (p === 'P1') return 'warning'
  return 'success'
}

// ... 其他代码 ...

// 新增这个函数来修复 type="" 的报错
const getCaseTypeTag = (type) => {
  const map = {
    'Negative': 'danger',    // 红色
    'Boundary': 'warning',   // 橙色
    'Functional': 'primary', // 蓝色
    'Performance': 'info'    // 灰色
  }
  // 如果匹配不到，默认返回 'primary' (蓝色)，千万不要返回 ''
  return map[type] || 'primary'
}

</script>

<style scoped>
.view-container {
  background: #fff;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

.status-dot {
  margin-right: 5px;
  vertical-align: middle;
}
</style>