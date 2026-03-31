<template>
  <div class="app-root">
    <GameView />
  </div>
</template>

<script setup>
import GameView from './components/GameView.vue'
</script>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  font-family: 'Crimson Pro', 'Georgia', serif;
  background: #070806;
  color: #e8e4dc;
  -webkit-font-smoothing: antialiased;
}

#app {
  min-height: 100vh;
}

.app-root {
  min-height: 100vh;
}
</style>