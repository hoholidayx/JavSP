<template>
  <div class="home-container">
    <h1>Item List</h1>

    <!-- 列表组件 -->
    <EntryList/>

    <!-- 其他内容 -->
    <div class="description">
      <p>Click items to view details</p>
    </div>
  </div>
</template>

<script setup>
import EntryList from "@/components/EntryList.vue";
</script>

<style scoped>
.home-container {
  text-align: center;
}

.description {
  margin-top: 2rem;
  color: #666;
}
</style>