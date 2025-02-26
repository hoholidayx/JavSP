<template>
  <!-- 应用容器 -->
  <div id="app">
    <!-- 全局导航 -->
    <nav class="global-nav">
      <router-link to="/">Home</router-link>
      <router-link to="/about">About</router-link>
    </nav>

    <!-- 路由视图容器 -->
    <!-- Vue 组件可能因为缓存或复用的原因没有重新渲染。可以使用 key 强制每次路由变化时重新渲染组件。-->
    <router-view :key="$route.fullPath"
                 v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component"/>
      </transition>
    </router-view>
  </div>
</template>

<script setup>
// 不需要额外逻辑时可以留空
</script>

<style>
#app {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  font-family: Arial, sans-serif;
}

.global-nav {
  padding: 1rem 0;
  margin-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.global-nav a {
  color: #2c3e50;
  text-decoration: none;
  padding: 0 1rem;
}

.global-nav a.router-link-exact-active {
  color: #42b983;
  font-weight: bold;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>