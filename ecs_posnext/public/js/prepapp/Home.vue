<template>
  <div class="order-app">
    <Preparing />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import Preparing from './components/Preparing.vue';

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
