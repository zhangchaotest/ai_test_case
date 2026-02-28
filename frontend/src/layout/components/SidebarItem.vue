<template>
  <!-- 🔥 修复点 1：同时检查 item.hidden 和 item.meta.hidden -->
  <template v-if="!item.hidden && !(item.meta && item.meta.hidden)">

    <!-- 情况1：只有一个需要显示的子路由 -> 渲染为点击项 -->
    <template v-if="hasOneShowingChild(item.children, item) && (!onlyOneChild.children || onlyOneChild.noShowingChildren)">
      <el-menu-item :index="resolvePath(onlyOneChild.path)">
        <el-icon v-if="onlyOneChild.meta && onlyOneChild.meta.icon">
          <component :is="onlyOneChild.meta.icon" />
        </el-icon>
        <template #title>
          <!-- 优先读取 meta.title -->
          <span>{{ onlyOneChild.meta?.title || onlyOneChild.title }}</span>
        </template>
      </el-menu-item>
    </template>

    <!-- 情况2：有多个子路由 -> 渲染为折叠菜单 -->
    <el-sub-menu v-else :index="resolvePath(item.path)">
      <template #title>
        <el-icon v-if="item.meta && item.meta.icon">
          <component :is="item.meta.icon" />
        </el-icon>
        <span>{{ item.meta?.title || item.title }}</span>
      </template>

      <sidebar-item
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :base-path="resolvePath(item.path)"
      />
    </el-sub-menu>

  </template>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  basePath: { type: String, default: '' }
})

const onlyOneChild = ref(null)

// src/layout/components/SidebarItem.vue

const hasOneShowingChild = (children = [], parent) => {
  // 1. 过滤隐藏的路由 (保持之前的修复)
  const showingChildren = children.filter(item => {
    if (item.hidden) return false
    if (item.meta && item.meta.hidden) return false
    return true
  })

  // 2. 如果只有一个子路由显示
  if (showingChildren.length === 1) {
    // 保存子路由
    onlyOneChild.value = showingChildren[0]
    return true
  }

  // 3. 【🔥 核心修复在这里】 如果没有子路由 (即它是最底层的菜单项)
  if (showingChildren.length === 0) {
    onlyOneChild.value = {
      ...parent,
      path: parent.path, // ❌ 之前写的是 '', 导致路径变成了根目录
                         // ✅ 现在改成 parent.path, 这样就是 'cases' 或 'requirements'
      noShowingChildren: true
    }
    return true
  }

  return false
}

// src/layout/components/SidebarItem.vue

const resolvePath = (routePath) => {
  if (isExternal(routePath)) {
    return routePath
  }

  // 1. 确保 basePath 以 / 结尾
  let basePath = props.basePath
  if (!basePath.endsWith('/')) {
    basePath += '/'
  }

  // 2. 确保子路径不以 / 开头 (防止双斜杠)
  const childPath = routePath.startsWith('/') ? routePath.slice(1) : routePath

  return basePath + childPath
}

// 简单的正则判断外链
const isExternal = (path) => {
  return /^(https?:|mailto:|tel:)/.test(path)
}
</script>