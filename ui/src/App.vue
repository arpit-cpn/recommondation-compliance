<script setup>
import Headbar from './scaffold/Headbar.vue';
import KeycloakSession from './scaffold/KeycloakSession.vue';
</script>

<template>
  <v-app>
    <headbar />
    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>
  </v-app>
  <KeycloakSession />
</template>
