import {createRouter, createWebHistory} from 'vue-router'
import Layout from '../layout/Layout.vue'

const routes = [
    {
        path: '/',
        component: Layout,
        redirect: '/requirements',
        // 根路由通常不显示在菜单，我们主要显示它的 children
        children: [
            {
                path: 'analysis',
                name: 'RequirementAnalysis',
                component: () => import('../views/RequirementAnalysis.vue'),
                meta: {title: '智能需求分析', icon: 'Cpu'}
            },
            {
                path: 'breakdown-list',
                name: 'BreakdownList',
                component: () => import('../views/BreakdownList.vue'),
                meta: {title: '需求拆解结果', icon: 'List'}
            },
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
            {
                path: 'execution',
                name: 'TestExecution',
                component: () => import('../views/TestExecution.vue'),
                meta: {title: '用例执行', icon: 'VideoPlay'} // 找一个播放按钮图标
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