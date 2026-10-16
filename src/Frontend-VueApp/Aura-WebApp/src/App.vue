<script setup>
import { ref } from 'vue'

const count = ref(0)
</script>

<template>
  <main>
    <h1>My Vue App</h1>
    <button @click="count++">CLICK</button>

    <h1 v-if="count>0">You clicked : {{count}} times</h1>
    <h1 v-else>RIGHT NOW</h1>
  </main>
</template>
