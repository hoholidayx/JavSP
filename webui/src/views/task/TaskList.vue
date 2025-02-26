<template>

  <!-- 操作按钮 -->
  <div class="action-bar">
    <button @click="clearAllTasks" class="action-button">
      清空所有任务记录
    </button>
  </div>

  <div class="task-list-container">
    <h1>任务列表</h1>
    <div class="task-grid">
      <div
          v-for="task in tasks"
          :key="task.id"
          class="task-card"
          @click="navigateToDetail(task.id)"
      >
        <div class="task-header">
          <span class="task-id">#{{ task.id }}</span>
          <span class="task-priority" :class="task.priority">{{ task.priority }}</span>
        </div>
        <h3 class="task-title">{{ task.title }}</h3>
        <p class="task-desc">{{ task.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'

const router = useRouter()

// 模拟任务数据
const tasks = ref([
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
])

const navigateToDetail = (taskId) => {
  router.push({
    name: 'Task/TaskDetail',
    params: {task_id: taskId}
  })
}

// actions
const clearAllTasks = () => {
  //清空所有任务记录
}

</script>

<style scoped>
.task-list-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.task-card {
  background: #fff;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s;
}

.task-card:hover {
  transform: translateY(-3px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.task-id {
  color: #666;
  font-size: 0.9em;
}

.task-priority {
  font-size: 0.8em;
  padding: 0.2em 0.5em;
  border-radius: 4px;
  text-transform: uppercase;
}

.task-priority.high {
  background: #ffebee;
  color: #c62828;
}

.task-priority.medium {
  background: #fff3e0;
  color: #ef6c00;
}

.task-priority.low {
  background: #e8f5e9;
  color: #2e7d32;
}

.task-title {
  margin: 0.5em 0;
  color: #2c3e50;
}

.task-desc {
  color: #666;
  font-size: 0.9em;
  line-height: 1.5;
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