<template>
  <div class="order-app">
    <Packing />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import Packing from './components/Packing.vue';

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
