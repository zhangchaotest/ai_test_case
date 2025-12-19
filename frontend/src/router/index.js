import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/requirements',
    // 根路由通常不显示在菜单，我们主要显示它的 children
    children: [
      {
        path: 'requirements',
        name: 'RequirementList',
        component: () => import('../views/RequirementList.vue'),
        meta: {
          title: '功能点管理',
          icon: 'Document' // 对应 Element Plus 图标名
        }
      },
      {
        path: 'cases',
        name: 'TestCaseList',
        component: () => import('../views/TestCaseList.vue'),
        meta: {
          title: '测试用例管理',
          icon: 'List'
        }
      },
    // 隐藏的详情页
      {
        path: 'detail/:id',
        meta: {
          title: '详情页',
          hidden: true // 🔥 推荐这种写法
        }
      }
    ]
  },
  // 示例：登录页，也不在左侧菜单显示
  {
    path: '/login',
    component: () => import('../views/TestCaseList.vue'), // 仅作示例
    hidden: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router