import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 通用表格 Hook
 * @param {Function} apiFunc - 请求接口的函数 (必须返回 { total, items })
 * @param {Object} initSearchParams - 初始搜索条件
 * @param {Boolean} autoLoad - 是否挂载时自动加载
 */
export function usePageTable(apiFunc, initSearchParams = {}, autoLoad = true) {
  // 核心数据
  const tableData = ref([])
  const total = ref(0)
  const loading = ref(false)

  // 分页参数
  const pagination = reactive({
    page: 1,
    size: 10
  })

  // 搜索参数
  const searchParams = reactive({ ...initSearchParams })

  // 核心加载函数
  const loadData = async () => {
    loading.value = true
    try {
      // 合并 分页参数 + 搜索参数
      const params = {
        page: pagination.page,
        size: pagination.size,
        ...searchParams
      }

      // 移除空值参数 (可选)
      for (const key in params) {
        if (params[key] === '' || params[key] === null) delete params[key]
      }

      const res = await apiFunc(params)

      // 兼容后端返回结构
      // 如果后端直接返回 items 数组 (没分页)，则 total = length
      // 如果后端返回标准 PageResponse，则取 total 和 items
      if (Array.isArray(res.data)) {
        tableData.value = res.data
        total.value = res.data.length
      } else {
        tableData.value = res.data.items || []
        total.value = res.data.total || 0
      }

    } catch (error) {
      console.error(error)
      ElMessage.error('数据加载失败')
    } finally {
      loading.value = false
    }
  }

  // 分页事件处理
  const handleSizeChange = (val) => {
    pagination.size = val
    pagination.page = 1 // 切换大小时重置到第一页
    loadData()
  }

  const handleCurrentChange = (val) => {
    pagination.page = val
    loadData()
  }

  // 搜索处理
  const handleSearch = () => {
    pagination.page = 1 // 搜索时重置到第一页
    loadData()
  }

  const handleReset = () => {
    // 重置搜索参数到初始值
    Object.keys(searchParams).forEach(key => {
      searchParams[key] = initSearchParams[key] || ''
    })
    handleSearch()
  }

  // 自动加载
  onMounted(() => {
    if (autoLoad) loadData()
  })

  return {
    tableData,
    total,
    loading,
    pagination,
    searchParams,
    loadData,
    handleSizeChange,
    handleCurrentChange,
    handleSearch,
    handleReset
  }
}