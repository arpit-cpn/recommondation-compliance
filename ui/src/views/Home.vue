<script setup>
import _ from 'lodash';
import { onMounted } from 'vue';
import Fetcher from '../Fetcher';
import useKeycloakStore from '../stores/keycloak';
import useNexusStore from '../stores/nexus';
import router from '../router';

const keycloakStore = useKeycloakStore();
const nexusStore = useNexusStore();

const http = new Fetcher('api/', async (options) => {
  await keycloakStore.ensureAccessToken();
  _.set(options, 'headers.Authorization', `Bearer ${keycloakStore.tokens.access_token}`);
});

const fetchMe = () => {
  http.get('me');
};

const fetchRoles = () => {
  http.get('me/roles');
};

onMounted(() => {
  if (keycloakStore.isActive && _.findIndex(nexusStore.orgs, { code: nexusStore.currentOrg }) > -1) {
    console.log('Pushing to dashboard');
    router.push({ name: 'dashboard', params: { org: nexusStore.currentOrg } });
  }
});

</script>

<template>
  <v-card title="Home">
    <template #text>
      <v-btn :to="{ name: 'keycloak' }" class="text-none">Keycloak Probe</v-btn>
      <v-btn @click="fetchMe" class="text-none ml-2">Me</v-btn>
      <v-btn @click="fetchRoles" class="text-none ml-2">Roles</v-btn>
    </template>
  </v-card>
</template>

<script>
export default {
  name: 'ViewHome',
};
</script>
