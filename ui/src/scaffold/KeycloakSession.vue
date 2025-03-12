<script setup>
import { onMounted, onBeforeUnmount } from 'vue';

import useKeycloakStore from '../stores/keycloak';
const keycloakStore = useKeycloakStore();

onMounted(() => {
  keycloakStore.init();
});

onBeforeUnmount(() => {
  keycloakStore.destroy();
});

</script>

<template>
  <iframe
    id="keycloak-session-iframe"
    :src="keycloakStore.urlSessionIframe"
    sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin"
    style="display: none;"
  />
</template>

<script>
export default {
  name: 'KeycloakSession',
};
</script>
