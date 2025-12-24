<template>
  <el-container class="layout-container">
    <!-- 左侧侧边栏 (保持不变) -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span>智能测试平台</span>
      </div>

      <el-menu
          :default-active="activeMenu"
          background-color="#2b3648"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
          class="el-menu-vertical"
      >
        <sidebar-item
            v-for="route in menuRoutes"
            :key="route.path"
            :item="route"
            :base-path="'/'"
        />
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部 Header -->
      <el-header height="40px" class="header">
        <!-- 🔥 核心修改：标签页区域 -->
        <div class="header-tags">
          <el-scrollbar>
            <div class="tags-wrapper">
              <el-tag
                  v-for="(tag, index) in tagsList"
                  :key="tag.fullPath"
                  :closable="tagsList.length > 1"
                  :effect="$route.path === tag.path ? 'dark' : 'plain'"
                  class="tag-item"
                  @click="handleTagClick(tag)"
                  @close="handleTagClose(tag, index)"
              >
                <!-- 这里的 title 需要路由 meta 里配置了 title 才能显示 -->
                {{ tag.title }}
              </el-tag>
            </div>
          </el-scrollbar>
        </div>
      </el-header>

      <!-- 主内容 (使用 keep-alive 可以缓存页面状态，可选) -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <!-- transition 和 keep-alive 是锦上添花的功能 -->
          <keep-alive :include="cachedViews">
            <component :is="Component" :key="$route.fullPath"/>
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {computed, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import SidebarItem from './components/SidebarItem.vue'

const route = useRoute()
const router = useRouter()
const cachedViews = ref([])
// --- 菜单逻辑 ---
const routes = router.options.routes
const menuRoutes = computed(() => {
  const layoutRoute = routes.find(r => r.path === '/')
  return layoutRoute ? layoutRoute.children : []
})
const activeMenu = computed(() => route.path)

// --- 🔥 核心修改：标签页逻辑 ---
const tagsList = ref([])

// 1. 添加标签
const addTags = () => {
  const {name, path, meta, fullPath} = route
  if (name) {
    // 现有逻辑：添加显示标签
    const isExist = tagsList.value.some(item => item.path === path)
    if (!isExist) {
      tagsList.value.push({
        title: meta.title || '未命名页面',
        path: path,
        fullPath: fullPath,
        name: name
      })
    }

    // 🔥 新增逻辑：添加到缓存列表
    // 只有当名字不在缓存里时才添加
    if (!cachedViews.value.includes(name)) {
      cachedViews.value.push(name)
    }
  }
}


// 2. 点击标签跳转
const handleTagClick = (tag) => {
  router.push(tag.fullPath)
}

// 3. 关闭标签
const handleTagClose = (tag, index) => {
  const length = tagsList.value.length - 1
  tagsList.value.splice(index, 1)

  // 🔥 新增逻辑：从缓存中移除
  // 这样下次再打开这个页面时，会重新加载，而不是显示旧数据
  const cacheIndex = cachedViews.value.indexOf(tag.name)
  if (cacheIndex > -1) {
    cachedViews.value.splice(cacheIndex, 1)
  }

  // ... 原有的跳转逻辑 ...
  if (tag.path === route.path) {
    if (index === 0) {
      if (tagsList.value.length > 0) {
         router.push(tagsList.value[0].fullPath)
      } else {
         router.push('/')
      }
    } else {
      router.push(tagsList.value[index - 1].fullPath)
    }
  }
}

// 4. 监听路由变化，自动添加标签
watch(
    () => route.path,
    () => {
      addTags()
    },
    {immediate: true} // 初始化时立即执行一次
)

</script>

<style scoped>
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

/* 顶部样式优化 */
.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  padding: 0; /* 去掉 padding 让 scrollbar 顶格 */
  box-shadow: 0 1px 4px rgba(0, 21, 41, .08);
}

.header-tags {
  flex: 1;
  overflow: hidden;
  padding: 5px 10px;
}

.tags-wrapper {
  display: flex;
  gap: 5px;
  flex-wrap: nowrap; /* 强制不换行 */
}

.tag-item {
  cursor: pointer;
  border-radius: 2px;
  user-select: none;
  transition: all 0.3s;
}

.tag-item:hover {
  opacity: 0.8;
}

/* 激活状态的 Tag 样式微调 */
.el-tag--dark {
  border-color: #409eff;
  background-color: #409eff;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
}

/* 简单的淡入淡出动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>