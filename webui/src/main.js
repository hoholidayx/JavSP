import {createApp} from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router' // 确保路由配置文件路径正确
import axios from 'axios';

// 创建Vue应用
const app = createApp(App)

// 注册路由
app.use(router)
app.use(ElementPlus)
// 挂载到DOM
app.mount('#app')
axios.defaults.withCredentials = true;

// 路由守卫
router.beforeEach(async (to, from, next) => {
    // 获取加密存储的toke
    // 获取所有Cookie字符串
    const cookieString = document.cookie;

    // 解析为对象
    function getCookies() {
        return cookieString.split(';').reduce((cookies, item) => {
            const [name, value] = item.trim().split('=');
            cookies[name] = decodeURIComponent(value);
            return cookies;
        }, {});
    }

    // 获取指定Cookie
    function getCookie(name) {
        const cookies = getCookies();
        return cookies[name] || null;
    }

    const authToken = getCookie('Auth-Token');
    console.log("Current Auth-Token=" + cookieString)
    // 需要登录验证的路由
    if (!authToken && to.matched.some(record => record.meta.requiresAuth !== false)) {
        // 记录原始路径并加密跳转参数
        const redirectPath = encodeURIComponent(btoa(to.fullPath));
        next({
            path: '/login',
            query: {redirect: redirectPath},
            // 防止浏览器历史记录污染
            replace: true
        });
    } else {
        next()
    }
});