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
            <el-option label="待审核" value="Pending"/>
            <el-option label="已通过" value="Pass"/>
            <el-option label="已拒绝" value="Reject"/>
          </el-select>
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="params.feature_name" placeholder="模糊搜索" clearable/>
        </el-form-item>
      </template>

      <!-- 表格列 -->
      <el-table-column prop="id" label="ID" width="60"/>
      <el-table-column prop="module_name" label="模块" width="100"/>
      <el-table-column prop="feature_name" label="功能名称" width="180" show-overflow-tooltip/>
      <el-table-column prop="description" label="功能描述" show-overflow-tooltip/>
<!--      <el-table-column prop="source_content" label="原始需求" width="200" show-overflow-tooltip/>-->
     <el-table-column label="原始需求" min-width="300">
        <template #default="{ row }">
          <ul class="ac-list">
            <!-- 使用新函数 formatTextToList -->
            <li v-for="(line, index) in formatTextToList(row.source_content)" :key="index">
              {{ line }}
            </li>
          </ul>
        </template>
      </el-table-column>

      <!-- 验收标准列 (保持类似逻辑) -->
      <el-table-column label="验收标准" min-width="250">
        <template #default="{ row }">
          <ul class="ac-list">
            <li v-for="(item, index) in formatTextToList(row.acceptance_criteria)" :key="index">
              {{ item }}
            </li>
          </ul>
        </template>
      </el-table-column>

<el-table-column prop="confidence_score" label="AI评分" width="100" align="center">
  <template #default="{ row }">
    <el-tooltip :content="row.review_comments || '无评审意见'" placement="top">
      <el-tag :type="getScoreColor(row.confidence_score)" effect="dark">
        {{ row.confidence_score }}
      </el-tag>
    </el-tooltip>
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
            <el-button link type="warning" @click="handleStatus(row, 'Reject')" v-if="row.review_status !== 'Reject'">
              拒绝
            </el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleStatus(row, 'Discard')">废弃</el-button>
          </div>
          <span v-else style="color: #67c23a; font-size: 12px;">已同步至功能点</span>
        </template>
      </el-table-column>
    </pro-table>

    <!-- 编辑弹窗 (复用) -->
    <el-dialog v-model="editVisible" title="编辑并重审" width="700px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="所属模块">
          <el-input v-model="editForm.module_name"/>
        </el-form-item>
        <el-form-item label="功能名称">
          <el-input v-model="editForm.feature_name"/>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="原始需求">
          <el-input
              v-model="editForm.source_content"
              type="textarea"
              :rows="3"
              placeholder="该功能点对应的原始需求片段"
          />
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
import {ref, reactive, onMounted} from 'vue'
import ProTable from '../components/ProTable.vue'
import {getBreakdownList, updateBreakdownItem, updateBreakdownStatus, getProjects} from '../api/api.js'
import {ElMessage, ElMessageBox} from 'element-plus'

const tableRef = ref(null)
const projects = ref([])
const initParams = reactive({})

const editVisible = ref(false)
const editForm = reactive({})

defineOptions({
  name: 'BreakdownList'
})

// 加载项目用于筛选
onMounted(async () => {
  const res = await getProjects()
  projects.value = res.data
})

// 状态操作
const handleStatus = async (row, status) => {
  const actionMap = {'Pass': '通过并同步', 'Reject': '拒绝', 'Discard': '废弃(隐藏)'}

  try {
    await ElMessageBox.confirm(
        `确定要【${actionMap[status]}】该条目吗？`,
        '状态变更',
        {type: status === 'Discard' ? 'error' : 'warning'}
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
  // 深拷贝，避免修改弹窗影响表格显示
  const formData = JSON.parse(JSON.stringify(row))

  // 🔥 核心优化：把 JSON 数组格式转为多行文本，方便用户编辑
  // 例如：["A", "B"] -> "A\nB"
  const acList = formatTextToList(formData.acceptance_criteria)
  formData.acceptance_criteria = acList.join('\n')

  // source_content 本身通常就是文本，但为了保险也处理一下
  // 如果之前存的是 JSON 格式，这里也会转成多行文本
  const scList = formatTextToList(formData.source_content)
  formData.source_content = scList.join('\n')

  Object.assign(editForm, formData)
  editVisible.value = true
}

// 提交编辑
const submitEdit = async () => {
  try {
    // 克隆表单数据
    const payload = { ...editForm }

    // 🔥 核心优化：保存前，把多行文本转回 JSON 数组字符串
    // 这样数据库里存的就是标准的 ["A", "B"] 格式，保持与 AI 生成格式一致

    // 1. 处理验收标准 (转 JSON)
    const acArray = payload.acceptance_criteria.split(/\r?\n/).filter(line => line.trim())
    payload.acceptance_criteria = JSON.stringify(acArray)

    // 2. 处理原始需求 (原始需求通常保留纯文本即可，如果你希望也存 JSON，可以用下面的逻辑)
    // 这里建议保留纯文本格式，因为原始需求通常是一大段话
    // payload.source_content = editForm.source_content

    // 调用 API
    await updateBreakdownItem(payload.id, payload)

    ElMessage.success('修改成功，状态已重置为待审核')
    editVisible.value = false
    tableRef.value?.refresh()
  } catch (e) {
    console.error(e)
    ElMessage.error('修改失败')
  }
}

// 辅助函数
const getStatusType = (s) => {
  const map = {'Pending': 'warning', 'Pass': 'success', 'Reject': 'danger'}
  return map[s] || 'info'
}
const getStatusText = (s) => {
  const map = {'Pending': '待审核', 'Pass': '已通过', 'Reject': '已拒绝'}
  return map[s] || s
}

// 尝试解析验收标准字符串
const parseCriteria = (str) => {
  if (!str) return []
  try {
    // 尝试解析 JSON 字符串
    const parsed = JSON.parse(str)
    // 如果解析出来是数组，直接返回
    if (Array.isArray(parsed)) {
      return parsed
    }
    // 如果不是数组（比如是纯文本），按换行符分割
    return String(str).split('\n')
  } catch (e) {
    // 解析失败（说明是普通字符串），按换行符分割
    return String(str).split('\n')
  }
}

// 判断是否需要列表展示
const isJSONList = (str) => {
  if (!str) return false
  try {
    const parsed = JSON.parse(str)
    return Array.isArray(parsed) && parsed.length > 0
  } catch (e) {
    return false
  }
}

// --- 文本格式化辅助函数 ---

// 将内容转换为数组，用于 v-for 展示
const formatTextToList = (content) => {
  if (!content) return []

  try {
    // 1. 尝试当做 JSON 数组解析
    const parsed = JSON.parse(content)
    if (Array.isArray(parsed)) {
      return parsed
    }
  } catch (e) {
    // 忽略 JSON 解析错误，说明是普通文本
  }

  // 2. 如果不是 JSON 数组，按换行符拆分
  // 过滤掉空行，处理 Windows/Unix 换行符
  return String(content)
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(line => line.length > 0)
}

const getScoreColor = (score) => {
  if (score >= 0.9) return 'success'  // 🟢 优秀
  if (score >= 0.7) return 'primary'  // 🔵 良好
  if (score >= 0.6) return 'warning'  // 🟠及格
  return 'danger'                     // 🔴 差
}
</script>

<style scoped>
.view-container {
  background: #fff;
  padding: 20px;
}
.ac-list {
  margin: 0;
  padding-left: 12px;
  list-style: none; /* 去掉默认圆点，我们自定义 */
}

.ac-list li {
  position: relative;
  line-height: 1.6; /* 增加行高，阅读更舒适 */
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

/* 自定义小圆点 */
.ac-list li::before {
  content: "";
  position: absolute;
  left: -10px;
  top: 8px; /* 居中对齐 */
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: #409eff; /* 蓝色圆点 */
}
</style>

