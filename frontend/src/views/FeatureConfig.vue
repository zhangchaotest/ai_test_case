<template>
  <div class="view-container">
    <h1>功能开关配置</h1>
    <el-card class="config-card">
      <el-form :model="configForm" label-width="180px">
        <el-form-item label="使用Dify知识库">
          <el-switch v-model="configForm.use_knowledge" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="使用LLM模型">
          <el-switch v-model="configForm.use_llm" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="使用测试维度分析">
          <el-switch v-model="configForm.use_test_dimension" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="使用上下文管理器">
          <el-switch v-model="configForm.use_context_manager" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="isLoading">保存配置</el-button>
          <el-button @click="loadConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { BASE_URL } from '../api/api.js'

const configForm = ref({
  use_knowledge: true,
  use_llm: true,
  use_test_dimension: true,
  use_context_manager: true
})

const isLoading = ref(false)

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch(`${BASE_URL}/config/feature`)
    if (!response.ok) throw new Error('获取配置失败')
    
    const data = await response.json()
    configForm.value = data
    ElMessage.success('配置加载成功')
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    isLoading.value = true
    const response = await fetch(`${BASE_URL}/config/feature`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(configForm.value)
    })
    
    if (!response.ok) throw new Error('保存配置失败')
    
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    isLoading.value = false
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.view-container {
  background: #fff;
  padding: 20px;
}

.config-card {
  margin-top: 20px;
}

.el-form-item {
  margin-bottom: 20px;
}
</style>