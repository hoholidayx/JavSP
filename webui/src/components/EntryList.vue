<template>
  <div class="item-list">
    <div
        v-for="(item, index) in menuItems"
        :key="index"
        class="list-item"
        @click="navigateToPage(item)"
    >
      <span class="icon" :style="{ color: item.color }">▶</span>
      {{ item.title }}
    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'

const router = useRouter()

// 菜单项配置
const menuItems = ref([
  {
    title: '开启新任务',
    path_name: 'Task/StartTask',
    color: '#42b983'
  },
  {
    title: '查看任务列表',
    path_name: 'Task/TaskList',
    color: '#647eff'
  },
])

// 路由跳转方法
const navigateToPage = (item) => {
  router.push({
    name: item.path_name,
    query: {  // 可选的查询参数
      source: 'home'
    }
  })
}
</script>

<style scoped>
.item-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.list-item {
  padding: 18px 25px;
  margin: 12px 0;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
}

.list-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.icon {
  margin-right: 15px;
  font-size: 0.8em;
  transition: transform 0.2s;
}

.list-item:hover .icon {
  transform: translateX(5px);
}
</style>