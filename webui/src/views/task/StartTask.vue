<template>
  <div class="container">
    <div class="input-section">
      <el-input
          v-model="taskContent"
          placeholder="请输入影片ID"
          clearable
          class="input-box"
      />
      <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
          class="submit-btn"
      >
        提交任务
      </el-button>
    </div>

    <div v-if="taskId"
         class="result-box"
         :class="{ 'copying': isCopying }"
         @click="copyTaskId">
      <el-tag type="success">任务创建成功</el-tag>
      <div class="task-id">
        任务 ID: {{ taskId }}
        <el-button
            type="text"
            icon="CopyDocument"
            @click="copyTaskId"
            class="copy-btn"
        />
      </div>
    </div>

    <el-dialog
        v-model="showError"
        title="错误提示"
        width="30%"
        center
    >
      <span>{{ errorMessage }}</span>
      <template #footer>
        <el-button @click="showError = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {ElMessage} from 'element-plus'
import axios from 'axios'

const taskContent = ref('')
const taskId = ref('')
const loading = ref(false)
const showError = ref(false)
const errorMessage = ref('')
const isCopying = ref(false) // 添加一个 ref 来跟踪复制状态

const handleSubmit = async () => {
  if (!taskContent.value.trim()) {
    ElMessage.warning('请输入任务内容')
    return
  }

  try {
    loading.value = true
    const response = await axios.get('http://localhost:7788/api/start_task', {
      params: {
        movie_dvdid: taskContent.value
      }
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.data.code === 0) {
      taskId.value = response.data.data.task_id
    } else {
      showError.value = true
      errorMessage.value = response.data.msg || '未知错误'
    }
  } catch (error) {
    showError.value = true
    errorMessage.value = error.response?.data?.msg ||
        error.message ||
        '请求失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

const copyTaskId = async () => {
  try {
    isCopying.value = true // 设置复制状态为 true
    await navigator.clipboard.writeText(taskId.value)
    ElMessage.success('任务 ID 已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  } finally {
    setTimeout(() => {
      isCopying.value = false // 延迟一段时间后重置复制状态
    }, 300)
  }
}
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 50px auto;
  padding: 30px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.input-section {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.input-box {
  flex: 1;
}

.submit-btn {
  width: 120px;
}

.result-box {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.task-id {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: monospace;
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.el-tag {
  margin-bottom: 10px;
}

.copy-btn {
  padding: 0;
  margin-left: 10px;
}

.result-box {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer; /* 添加鼠标指针样式 */
  transition: background-color 0.3s ease; /* 添加过渡效果 */
}

.result-box.copying {
  background-color: #f0f9eb; /* 复制时的背景色 */
}
</style>