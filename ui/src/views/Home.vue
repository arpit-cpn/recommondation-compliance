<script setup>
import _ from 'lodash';
import Fetcher from '../Fetcher';
import useKeycloakStore from '../stores/keycloak';

const keycloakStore = useKeycloakStore();

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
