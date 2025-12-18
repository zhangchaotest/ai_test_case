<template>
  <div class="container">
    <el-header>
      <h2>🤖 AI 智能测试用例生成平台</h2>
    </el-header>

    <el-main>
      <!-- 需求列表表格 -->
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>需求列表 (Requirements)</span>
            <el-button type="primary" @click="fetchData">刷新列表</el-button>
          </div>
        </template>

        <el-table :data="requirements" stripe style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="module_name" label="模块" width="120" />
          <el-table-column prop="feature_name" label="功能名称" width="200" />
          <el-table-column prop="description" label="功能描述" show-overflow-tooltip />
          <el-table-column prop="priority" label="优先级" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.priority === 'P0' ? 'danger' : 'warning'">
                {{ scope.row.priority }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="用例数" width="100">
            <template #default="scope">
              <el-tag effect="dark" type="info">{{ scope.row.case_count }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="250">
            <template #default="scope">
              <!-- 生成按钮 -->
              <el-button
                type="primary"
                size="small"
                :loading="generatingId === scope.row.id"
                @click="handleGenerate(scope.row.id)"
              >
                <el-icon><MagicStick /></el-icon> AI 生成
              </el-button>

              <!-- 查看按钮 -->
              <el-button
                type="success"
                size="small"
                :disabled="scope.row.case_count === 0"
                @click="handleViewCases(scope.row)"
              >
                <el-icon><View /></el-icon> 查看用例
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-main>

    <!-- 侧边栏：展示测试用例详情 -->
    <el-drawer v-model="drawerVisible" title="测试用例详情" size="60%">
      <template #header>
        <h3>{{ currentReqName }} - 测试用例列表</h3>
      </template>

      <div v-if="testCases.length === 0" class="empty-text">暂无数据</div>

      <el-collapse v-model="activeNames" accordion>
        <el-collapse-item
          v-for="(item, index) in testCases"
          :key="item.id"
          :name="index"
        >
          <template #title>
            <div class="case-header">
              <el-tag size="small" :type="getTypeTag(item.case_type)" style="margin-right: 10px">
                {{ item.case_type }}
              </el-tag>
              <span class="case-title">[{{ item.priority }}] {{ item.case_title }}</span>
            </div>
          </template>

          <div class="case-content">
            <p><strong>前置条件：</strong> {{ item.pre_condition || '无' }}</p>

            <!-- 步骤表格 (解析 JSON 显示) -->
            <el-table :data="item.steps" border size="small" style="margin: 10px 0">
              <el-table-column prop="step_id" label="#" width="50" />
              <el-table-column prop="action" label="测试步骤" />
              <el-table-column prop="expected" label="预期结果" />
            </el-table>

            <p><strong>总体预期：</strong> {{ item.expected_result }}</p>

            <div v-if="item.test_data && Object.keys(item.test_data).length" class="test-data">
              <strong>测试数据：</strong>
              <pre>{{ item.test_data }}</pre>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { MagicStick, View } from '@element-plus/icons-vue'
import { getRequirements, generateCases, getTestCases } from './api/api.js'
import { ElMessage } from 'element-plus'

const requirements = ref([])
const loading = ref(false)
const generatingId = ref(null)

// 抽屉相关
const drawerVisible = ref(false)
const testCases = ref([])
const currentReqName = ref('')
const activeNames = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getRequirements()
    requirements.value = res.data
  } catch (error) {
    ElMessage.error('获取需求列表失败')
  } finally {
    loading.value = false
  }
}

const handleGenerate = async (id) => {
  generatingId.value = id
  ElMessage.info('AI 正在思考并生成用例，请耐心等待...')
  try {
    await generateCases(id)
    ElMessage.success('生成完成！用例已入库')
    await fetchData() // 刷新列表看数量变化
  } catch (error) {
    ElMessage.error('生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generatingId.value = null
  }
}

const handleViewCases = async (row) => {
  currentReqName.value = row.feature_name
  drawerVisible.value = true
  testCases.value = []
  try {
    const res = await getTestCases(row.id)
    testCases.value = res.data
    // 默认展开第一个
    if (testCases.value.length > 0) activeNames.value = 0
  } catch (error) {
    ElMessage.error('获取用例详情失败')
  }
}

const getTypeTag = (type) => {
  const map = {
    'Functional': '',
    'Negative': 'danger',
    'Boundary': 'warning',
    'Performance': 'info'
  }
  return map[type] || 'info'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.case-header { font-weight: bold; }
.case-title { font-size: 14px; }
.case-content { padding: 0 10px; }
.test-data { background: #f4f4f5; padding: 10px; border-radius: 4px; margin-top: 10px; }
pre { margin: 0; font-family: monospace; }
</style>