import {createApp} from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router' // 确保路由配置文件路径正确

// 创建Vue应用
const app = createApp(App)

// 注册路由
app.use(router)
app.use(ElementPlus)

// 挂载到DOM
app.mount('#app')
