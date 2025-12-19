import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 1. 确保引入了 router
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 注册图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 2. 【关键】必须先 use(router)，然后再 mount('#app')
app.use(router)
app.use(ElementPlus)

// 3. 最后一步才是挂载
app.mount('#app')