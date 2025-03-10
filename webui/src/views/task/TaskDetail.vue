<template>

  <!-- 操作按钮 -->
  <div class="action-bar">
    <button @click="goBack" class="action-button">
      ← 返回任务列表
    </button>
  </div>

  <div class="task-detail-container">
    <!-- 基本信息展示 -->
    <div class="task-info">
      <h2>任务详情</h2>
      <div class="info-item">
        <label>任务ID：</label>
        <span>{{ taskData.taskId }}</span>
      </div>
      <div class="info-item">
        <label>任务状态：</label>
        <span class="state-success">
          {{ taskData.stateText }}
        </span>
      </div>
    </div>

    <!-- 任务操作区域 -->
    <div class="task-actions">
      <el-button type="primary" @click="showTaskLogs">查看任务日志</el-button>
      <el-button type="danger" @click="deleteTask">删除任务</el-button>
    </div>

    <!-- 影片列表操作 -->
    <div class="movie-operations">
      <h3>关联影片列表</h3>
      <el-radio-group v-model="selectedMovieId">
        <el-radio
            v-for="movieId in movieIds"
            :key="movieId"
            :label="movieId"
            class="movie-radio"
        >
          {{ movieId }}
        </el-radio>
      </el-radio-group>

      <el-button
          type="primary"
          :disabled="!selectedMovieId"
          @click="showMovieDirectory"
      >
        查看输出目录
      </el-button>
    </div>

    <!-- 日志对话框 -->
    <el-dialog v-model="logDialogVisible" title="任务日志" width="70%">
      <pre class="log-content">{{ taskLogs }}</pre>
    </el-dialog>

  </div>
</template>

<script setup>
import {useRoute, useRouter} from 'vue-router'
import {ref} from "vue";
import {ElLoading, ElMessage, ElMessageBox} from "element-plus";

const route = useRoute()
const router = useRouter()

const goBack = () => {
  // 两种返回方式任选其一：
  // 1. 直接返回列表页（推荐）
  router.push({name: 'Task/TaskList'})

  // 2. 返回上一页（如果可能从其他页面跳转过来）
  // router.go(-1)
}

const taskId = route.params.task_id;

const movieIds = route.query.movie_ids;

const stateText = route.query.state_text
// 任务数据
const taskData = ref({taskId: taskId, movieIds: movieIds, stateText: stateText})
// 选中的影片ID
const selectedMovieId = ref('')

// 日志相关
const logDialogVisible = ref(false)
const taskLogs = ref({})

/**
 * 删除当前任务
 * @returns {Promise<void>}
 */
const deleteTask = async () => {
  try {
    const response = await fetch(
        `http://127.0.0.1:7788/api/remove_task?task_id=${taskData.value.taskId}`
    )
    const result = await response.json()

    if (result.code === 0) {
      ElMessage.info('删除成功')
    } else {
      ElMessage.error(`删除失败：${result.msg}`)
    }
  } catch (error) {
    ElMessage.error(`请求失败：${error.message}`)
  } finally {
    goBack()
  }
}

// 查看任务日志
const showTaskLogs = async () => {
  const loading = ElLoading.service({
    lock: true,
    text: '获取日志中...'
  })

  try {
    const response = await fetch(
        `http://127.0.0.1:7788/api/get_task_logs?task_id=${taskData.value.taskId}`
    )
    const result = await response.json()

    if (result.code === 0) {
      taskLogs.value = result.data.log_list
      logDialogVisible.value = true
    } else {
      ElMessage.error(`获取日志失败：${result.msg}`)
    }
  } catch (error) {
    ElMessage.error(`请求失败：${error.message}`)
  } finally {
    loading.close()
  }
}

// 查看输出目录
const showMovieDirectory = async () => {
  const loading = ElLoading.service({
    lock: true,
    text: '获取目录信息...'
  })

  try {
    const params = new URLSearchParams({
      task_id: taskData.value.taskId,
      movie_dvdid: selectedMovieId.value
    })

    const response = await fetch(
        `http://127.0.0.1:7788/api/list_movie_dir?${params}`
    )
    const result = await response.json()
    if (result.code === 0) {
      // 根据实际返回数据结构调整展示方式
      ElMessageBox.alert(
          `<pre>${JSON.stringify(result.data, null, 2)}</pre>`,
          '目录结构',
          {
            dangerouslyUseHTMLString: true,
            customClass: 'dir-dialog'
          }
      )
    } else {
      ElMessage.error(`获取失败：${result.msg}`)
    }
  } catch (error) {
    ElMessage.error(`请求失败：${error.message}`)
  } finally {
    loading.close()
  }
}
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.info-item {
  margin: 15px 0;
  font-size: 16px;
}

.info-item label {
  font-weight: bold;
  margin-right: 10px;
}

.task-actions {
  margin: 30px 0;
  display: flex;
  gap: 15px;
}

.movie-operations {
  margin-top: 40px;
}

.movie-radio {
  display: block;
  margin: 10px 0;
}

.log-content {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre-wrap;
}

/* 状态样式保持与列表页一致 */
.state-init {
  color: #666;
}

.state-running {
  color: #1677ff;
}

.state-failed {
  color: #ff4d4f;
}

.state-success {
  color: #52c41a;
}

/* 自定义对话框样式 */
:deep(.dir-dialog) {
  width: 70%;
  max-width: 800px;
}

:deep(.dir-dialog pre) {
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-row label {
  width: 80px;
  color: #666;
  font-weight: 500;
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