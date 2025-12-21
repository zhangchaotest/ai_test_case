<template>
  <div class="pro-table">
    <!-- 1. 顶部搜索栏 (使用 slot 插槽，因为每个页面的搜索项不一样) -->
    <el-card shadow="never" class="filter-container" v-if="$slots.search">
      <el-form :inline="true" :model="searchParams">
        <!-- 默认插槽：放 input/select 等 -->
        <slot name="search" :params="searchParams"></slot>

        <!-- 固定按钮 -->
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <slot name="buttons"></slot> <!-- 额外的按钮如“导出” -->
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 2. 表格主体 -->
    <el-card shadow="never" class="table-card">
      <!-- 工具栏插槽 (如新增按钮) -->
      <div v-if="$slots.toolbar" class="toolbar">
        <slot name="toolbar"></slot>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
        v-bind="$attrs"
      >
        <!-- 这里的 slot 用于自定义列 -->
        <slot></slot>
      </el-table>

      <!-- 3. 翻页器 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { Search, Refresh } from '@element-plus/icons-vue'
import { usePageTable } from '../hooks/usePageTable'

const props = defineProps({
  // 必传：API 请求函数
  api: { type: Function, required: true },
  // 初始搜索参数
  initParam: { type: Object, default: () => ({}) }
})

// 使用刚才定义的 Hook
// 这里把内部状态解构出来，暴露给父组件（通过 expose 或 slot 作用域）
const {
  tableData,
  total,
  loading,
  pagination,
  searchParams,
  handleSearch,
  handleReset,
  handleSizeChange,
  handleCurrentChange,
  loadData // 暴露刷新方法
} = usePageTable(props.api, props.initParam)

// 暴露给父组件，父组件可以通过 ref 调用 (比如 refresh)
defineExpose({
  refresh: loadData,
  tableData
})
</script>

<style scoped>
.filter-container { margin-bottom: 10px; }
.pagination-wrapper { margin-top: 20px; display: flex; justify-content: flex-end; }
.toolbar { margin-bottom: 15px; }
</style>