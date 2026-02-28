import {createRouter, createWebHistory} from 'vue-router'
import Layout from '../layout/Layout.vue'

const routes = [
    {
        path: '/',
        component: Layout,
        redirect: '/features/requirements',
        // 根路由通常不显示在菜单，我们主要显示它的 children
        children: [
            // 功能菜单
            {
                path: 'features',
                name: 'Features',
                meta: {title: '智能工坊', icon: 'Menu'},
                children: [
                    {
                        path: 'analysis',
                        name: 'RequirementAnalysis',
                        component: () => import('../views/RequirementAnalysis.vue'),
                        meta: {title: '需求智能解析', icon: 'Cpu'}
                    },
                    {
                        path: 'breakdown-list',
                        name: 'BreakdownList',
                        component: () => import('../views/BreakdownList.vue'),
                        meta: {title: '需求解构中心', icon: 'List'}
                    },
                    {
                        path: 'requirements',
                        name: 'RequirementList',
                        component: () => import('../views/RequirementList.vue'),
                        meta: {
                            title: '功能模块管理',
                            icon: 'Document' // 对应 Element Plus 图标名
                        }
                    },
                    {
                        path: 'cases',
                        name: 'TestCaseList',
                        component: () => import('../views/TestCaseList.vue'),
                        meta: {
                            title: '用例矩阵',
                            icon: 'List'
                        }
                    },
                    {
                        path: 'execution',
                        name: 'TestExecution',
                        component: () => import('../views/TestExecution.vue'),
                        meta: {title: '执行引擎', icon: 'VideoPlay'} // 找一个播放按钮图标
                    }
                ]
            },
            // 配置菜单
            {
                path: 'configs',
                name: 'Configs',
                meta: {title: '配置中心', icon: 'Setting'},
                children: [
                    {
                        path: 'prompts',
                        name: 'PromptManagement',
                        component: () => import('../views/PromptManagement.vue'),
                        meta: {title: '提示词实验室', icon: 'Document'} // 对应 Element Plus 图标名
                    },
                    {
                        path: 'features',
                        name: 'FeatureConfig',
                        component: () => import('../views/FeatureConfig.vue'),
                        meta: {title: '功能控制面板', icon: 'Switch'} // 对应 Element Plus 图标名
                    }
                ]
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