<template>

  <!-- 操作按钮 -->
  <div class="action-bar">
    <button @click="goBack" class="action-button">
      ← 返回任务列表
    </button>
  </div>

  <div class="task-detail-container">
    <div class="detail-content">
      <h1>任务详情 #{{ taskId }}</h1>

      <!-- 模拟详情内容 -->
      <div class="detail-card">
        <div class="detail-row">
          <label>标题：</label>
          <span>{{ currentTask?.title }}</span>
        </div>
        <div class="detail-row">
          <label>状态：</label>
          <span class="task-status">{{ currentTask?.status }}</span>
        </div>
        <div class="detail-row">
          <label>描述：</label>
          <p class="task-description">{{ currentTask?.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'

const router = useRouter()
const route = useRoute()

// 通过 props 接收参数
const props = defineProps({
  task_id: {
    type: [String, Number],
    required: true
  }
})

// 模拟数据获取
const tasks = [
  // 与 TaskList.vue 中的模拟数据保持一致
  {
    id: 1,
    title: '开发登录模块',
    description: '实现用户认证功能',
    priority: 'high',
    status: '进行中'
  },
  {
    id: 2,
    title: '编写单元测试',
    description: '完成核心模块的测试用例',
    priority: 'medium',
    status: '待开始'
  },
  {
    id: 3,
    title: '优化性能',
    description: '减少首屏加载时间',
    priority: 'low',
    status: '已完成'
  }
]

// 获取当前任务详情
const currentTask = computed(() =>
    tasks.find(task => task.id === Number(props.task_id))
)

const goBack = () => {
  // 两种返回方式任选其一：
  // 1. 直接返回列表页（推荐）
  router.push({name: 'Task/TaskList'})

  // 2. 返回上一页（如果可能从其他页面跳转过来）
  // router.go(-1)
}
</script>

<style scoped>
.task-detail-container {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 2rem;
}

.detail-content {
  flex: 1;
}

.detail-card {
  background: #fff;
  border-radius: 10px;
  padding: 2rem;
  margin-top: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.detail-row {
  margin: 1.5rem 0;
  display: flex;
  align-items: flex-start;
}

.detail-row label {
  width: 80px;
  color: #666;
  font-weight: 500;
}

.task-status {
  padding: 0.3em 0.8em;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 0.9em;
}

.action-bar {
  border-top: 1px solid #eee;
  padding: 2rem 0;
  margin-top: 2rem;
  text-align: center;
}

.action-button {
  background: none;
  border: none;
  color: #42b983;
  font-size: 1em;
  cursor: pointer;
  padding: 0.8em 1.5em;
  border-radius: 6px;
  transition: background 0.2s;
}

.action-button:hover {
  background: #f5f5f5;
}
</style>