<template>
  <div class="order-app">
    <Pending />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import Pending from './components/Pending.vue';

onMounted(() => {
  $('.page-head').remove();
  $('.navbar.navbar-default.navbar-fixed-top').remove();
});
</script>

<style scoped>
.order-app {
  margin-top: 0;
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
}
</style>
