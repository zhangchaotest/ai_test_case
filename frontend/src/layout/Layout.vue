<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span>智能测试平台</span>
      </div>

      <!-- 菜单容器 -->
      <el-menu
          :default-active="activeMenu"
          background-color="#2b3648"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
          class="el-menu-vertical"
      >
        <!-- 🔥 核心修改：循环路由配置 -->
        <sidebar-item
            v-for="route in menuRoutes"
            :key="route.path"
            :item="route"
            :base-path="'/'"
        />
        <!-- ✅ 正确：强制指定基础路径为根目录 '/' -->
      </el-menu>
    </el-aside>

    <el-container>
      <!-- ... Header 和 Main 内容保持不变 ... -->
      <el-header height="40px" class="header">
        <div class="header-tags">
          <el-tag closable effect="dark" class="active-tag">{{ $route.meta.title }}</el-tag>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view/>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import SidebarItem from './components/SidebarItem.vue' // 引入刚才写的组件

const route = useRoute()
const router = useRouter()

// 1. 获取所有路由配置
const routes = router.options.routes

// 2. 提取需要显示的菜单
// 在你的结构中，Layout 是根路由 '/'，我们需要显示它的 children
// 如果你的结构更复杂，这里可能需要调整过滤逻辑
const menuRoutes = computed(() => {
  // 找到 Layout 对应的那个根路由（通常是 path: '/'）
  const layoutRoute = routes.find(r => r.path === '/')
  return layoutRoute ? layoutRoute.children : []
})

// 3. 高亮当前激活菜单
const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
/* ... 样式保持不变 ... */
.layout-container {
  height: 100vh;
}

.aside {
  background-color: #2b3648;
  overflow-x: hidden;
}

.logo {
  height: 50px;
  line-height: 50px;
  color: #fff;
  padding-left: 20px;
  font-weight: bold;
  font-size: 14px;
  background: #2b3648;
}

.el-menu-vertical {
  border-right: none;
}

.header {
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.active-tag {
  border-radius: 0;
}

.main-content {
  background: #fff;
  padding: 20px;
}
</style>