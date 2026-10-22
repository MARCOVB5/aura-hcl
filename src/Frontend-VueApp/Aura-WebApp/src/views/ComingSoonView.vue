<script setup>
defineProps({
  title: { type: String, required: true },
})
</script>

<template>
  <header class="page-header">
    <h2 class="service-name">Service de réanimation</h2>
    <div class="title-row">
      <div>
        <h1 class="page-title">{{ title }}</h1>
        <p class="page-description">Cette page n’est pas encore disponible.</p>
      </div>
    </div>
  </header>
</template>
