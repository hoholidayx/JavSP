import {createRouter, createWebHistory} from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: () => import('@/views/Home.vue')
    },
    {
        path: '/task/start_task',
        name: 'Task/StartTask',
        component: () => import('@/views/task/StartTask.vue'),
        props: true
    },
    {
        path: '/task/task_list',
        name: 'Task/TaskList',
        component: () => import('@/views/task/TaskList.vue'),
        props: true
    }, ,
    {
        path: '/task/detail/:task_id',
        name: 'Task/TaskDetail',
        component: () => import('@/views/task/TaskDetail.vue'),
        props: true
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router