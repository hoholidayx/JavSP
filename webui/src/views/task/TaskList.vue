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
          :key="task.task_id"
          class="task-card"
          @click="navigateToDetail(task.task_id,task.movie_ids,stateText(task.state))"
      >
        <div class="task-header">
          <span class="task-id">任务ID: {{ task.task_id }}</span>
          <span class="task-state" :class="stateClass(task.state)">
            {{ stateText(task.state) }}
          </span>
        </div>
        <h3 class="task-title">关联影片ID</h3>
        <div class="movie-list">
          <span v-for="movieId in task.movie_ids" :key="movieId" class="movie-id">
            {{ movieId }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref, toRaw} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'

const router = useRouter()
const tasks = ref([])

// 状态映射配置
const stateMap = {
  0: '等待开始',
  1: '进行中',
  2: '已完成（失败）',
  3: '已完成（成功）'
}

// 状态样式映射
const stateClassMap = {
  0: 'state-init',
  1: 'state-running',
  2: 'state-failed',
  3: 'state-success'
}

// 获取任务列表
const fetchTasks = async () => {
  try {
    const response = await fetch('http://127.0.0.1:7788/api/get_task_list')
    const result = await response.json()
    if (result.code === 0) {
      tasks.value = result.data.task_list
    } else {
      console.error('获取任务列表失败:', result.msg)
    }
  } catch (error) {
    console.error('请求失败:', error)
  }
}

// 状态文本转换
const stateText = (state) => stateMap[state] || '未知状态'

// 状态样式
const stateClass = (state) => stateClassMap[state] || ''

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
})

const navigateToDetail = (taskId, movieIds, stateText) => {
  router.push({
    name: 'Task/TaskDetail',
    params: {task_id: taskId,},
    query: {movie_ids: toRaw(movieIds), state_text: stateText}
  })
}

// actions
const clearAllTasks = async () => {
  //清空所有任务记录
  try {
    const response = await fetch('http://127.0.0.1:7788/api/clear_all_tasks', {
      method: 'POST'
    })

    const result = await response.json()

    if (result.code === 0) {
      ElMessage({
        message: '所有任务记录已清空',
        type: 'success',
        duration: 3000
      })
      await fetchTasks()
    } else {
      ElMessage({
        message: `清空失败：${result.msg}`,
        type: 'error',
        duration: 3000
      })
    }
  } catch (error) {
    ElMessage({
      message: `请求失败：${error.message}`,
      type: 'error',
      duration: 3000
    })
  }
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

/* 新增状态样式 */
.task-state {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
}

.state-init {
  background-color: #f0f0f0;
  color: #666;
}

.state-running {
  background-color: #e6f4ff;
  color: #1677ff;
}

.state-failed {
  background-color: #fff2f0;
  color: #ff4d4f;
}

.state-success {
  background-color: #f6ffed;
  color: #52c41a;
}

.movie-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.movie-id {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

/* 保持原有样式 */
.task-list-container {
  padding: 20px;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.task-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.3s;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-id {
  font-size: 0.9em;
  color: #666;
}
</style>