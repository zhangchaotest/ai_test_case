<template>
  <div class="view-container">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">📝 提示词管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus/></el-icon>
            新增提示词
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="search-panel">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="领域">
            <el-select v-model="searchForm.domain" placeholder="全部" clearable style="width: 120px">
              <el-option label="全部" value=""/>
              <el-option label="基础测试" value="base"/>
              <el-option label="Web应用测试" value="web"/>
              <el-option label="API测试" value="api"/>
            </el-select>
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="searchForm.type" placeholder="全部" clearable style="width: 100px">
              <el-option label="全部" value=""/>
              <el-option label="生成器" value="generator"/>
              <el-option label="评审器" value="reviewer"/>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadPrompts">
              <el-icon><Search/></el-icon>
              查询
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 提示词列表 -->
      <el-table :data="prompts" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"/>
        <el-table-column prop="name" label="名称" width="180"/>
        <el-table-column prop="domain" label="领域" width="120">
          <template #default="{ row }">
            <el-tag :type="getDomainType(row.domain)">{{ getDomainLabel(row.domain) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip/>
        <el-table-column prop="created_at" label="创建时间" width="180"/>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">
              <el-icon><Edit/></el-icon>
              编辑
            </el-button>
            <el-button type="danger" link @click="confirmDelete(row.id, row.name)">
              <el-icon><Delete/></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑提示词对话框 -->
    <el-dialog
        v-model="dialogVisible"
        :title="dialogTitle"
        width="600px"
    >
      <el-form :model="form" label-width="100px" class="dialog-form">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="请输入提示词名称"/>
        </el-form-item>
        <el-form-item label="领域" required>
          <el-select v-model="form.domain" placeholder="请选择领域">
            <el-option label="基础测试" value="base"/>
            <el-option label="Web应用测试" value="web"/>
            <el-option label="API测试" value="api"/>
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type" placeholder="请选择类型">
            <el-option label="生成器" value="generator"/>
            <el-option label="评审器" value="reviewer"/>
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="请输入提示词描述"/>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
              v-model="form.content"
              type="textarea"
              :rows="6"
              placeholder="请输入提示词内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePrompt">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { BASE_URL } from '../api/api.js'

// 状态定义
const prompts = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const dialogTitle = ref('新增提示词')
const form = reactive({
  id: null,
  name: '',
  content: '',
  domain: 'base',
  type: 'generator',
  description: ''
})
const searchForm = reactive({
  domain: '',
  type: ''
})

// 加载提示词列表
const loadPrompts = async () => {
  try {
    let url = `${BASE_URL}/prompts`
    const params = []
    
    if (searchForm.domain) {
      params.push(`domain=${searchForm.domain}`)
    }
    if (searchForm.type) {
      params.push(`type=${searchForm.type}`)
    }
    
    if (params.length > 0) {
      url += `?${params.join('&')}`
    }
    
    const response = await fetch(url)
    if (!response.ok) throw new Error('获取提示词列表失败')
    
    const data = await response.json()
    prompts.value = data
    total.value = data.length
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 打开新增对话框
const openCreateDialog = () => {
  form.id = null
  form.name = ''
  form.content = ''
  form.domain = 'base'
  form.type = 'generator'
  form.description = ''
  dialogTitle.value = '新增提示词'
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (row) => {
  form.id = row.id
  form.name = row.name
  form.content = row.content
  form.domain = row.domain
  form.type = row.type
  form.description = row.description
  dialogTitle.value = '编辑提示词'
  dialogVisible.value = true
}

// 保存提示词
const savePrompt = async () => {
  if (!form.name) return ElMessage.warning('请输入提示词名称')
  if (!form.content) return ElMessage.warning('请输入提示词内容')
  
  try {
    let url, method
    if (form.id) {
      url = `${BASE_URL}/prompts/${form.id}`
      method = 'PUT'
    } else {
      url = `${BASE_URL}/prompts`
      method = 'POST'
    }
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: form.name,
        content: form.content,
        domain: form.domain,
        type: form.type,
        description: form.description
      })
    })
    
    if (!response.ok) throw new Error('保存提示词失败')
    
    ElMessage.success(form.id ? '提示词更新成功' : '提示词创建成功')
    dialogVisible.value = false
    loadPrompts()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 确认删除
const confirmDelete = (id, name) => {
  ElMessageBox.confirm(
    `确定要删除提示词 "${name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await fetch(`${BASE_URL}/prompts/${id}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) throw new Error('删除提示词失败')
      
      ElMessage.success('提示词删除成功')
      loadPrompts()
    } catch (error) {
      ElMessage.error(error.message)
    }
  })
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  loadPrompts()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  loadPrompts()
}

// 辅助函数
const getDomainLabel = (domain) => {
  const labels = {
    'base': '基础测试',
    'web': 'Web应用测试',
    'api': 'API测试'
  }
  return labels[domain] || domain
}

const getDomainType = (domain) => {
  const types = {
    'base': 'info',
    'web': 'success',
    'api': 'warning'
  }
  return types[domain] || 'info'
}

const getTypeLabel = (type) => {
  return type === 'generator' ? '生成器' : '评审器'
}

const getTypeType = (type) => {
  return type === 'generator' ? 'primary' : 'danger'
}

// 初始化
onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.view-container {
  padding: 20px;
  background: #f5f7fa;
}

.page-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.search-panel {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.search-form {
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-form {
  margin-top: 20px;
}
</style>