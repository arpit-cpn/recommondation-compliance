<script setup>
import _ from 'lodash';
import { onMounted, ref } from 'vue';
import { formatDistanceToNow } from 'date-fns';
import { useRoute, useRouter } from 'vue-router';
import useKeycloakStore from '../stores/keycloak';
import Fetcher from '../Fetcher';

const route = useRoute();
const router = useRouter();
const keycloakStore = useKeycloakStore();
const routeTest = ref({
  payload: 'about',
  options: ['orgs', 'about', 'docs/benchmark', 'orgs/ccm/sites/carlisle/lines', 'tenants/'],
});

const isOverlayVisible = ref(true);

const http = new Fetcher('api/tfnexus/', async (options) => {
  await keycloakStore.ensureAccessToken();
  _.set(options, 'headers.Authorization', `Bearer ${keycloakStore.tokens.access_token}`);
});

onMounted(() => {
  if (route.query.session_state) {
    keycloakStore.fetchTokens(route.query.session_state).then(() => {
      // router.push({ query: null });
      router.push({ name: 'home' });
    });
  }
});

const fetchRouteTest = async () => {
  fetch(`api/tfnexus/${routeTest.value.payload}`, {
    headers: {
      Authorization: `Bearer ${keycloakStore.tokens.access_token}`,
    },
  });
};

const fetchUserinfo = () => {
  http.get('/auth/keycloak/userinfo');
  http.get('/auth/keycloak/userinfo');
};

const fetchTanents = () => {
  http.get('v1/tenants');
};

</script>
<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card title="Keycloak">
          <v-overlay v-model="isOverlayVisible" class="align-center justify-center bg-white" contained opacity="0.2" />
          <template #append>
            <v-btn href="/auth/keycloak/login" v-if="!keycloakStore.isActive">Login</v-btn>
            <template v-else>
              <div class="d-flex flex-row">
                <v-combobox class="ma-1" v-model="routeTest.payload" density="compact" variant="outlined" hide-details width="300" flat placeholder="route to test" :items="routeTest.options" />
                <v-btn class="ma-1" @click="fetchTanents">Tanents</v-btn>
                <v-btn class="ma-1" @click="fetchRouteTest">Test</v-btn>
                <v-btn class="ma-1" @click="fetchUserinfo">User info (access token ensured)</v-btn>
                <v-btn class="ma-1" @click="keycloakStore.fetchUserinfo">User info</v-btn>
                <v-btn class="ma-1" @click="keycloakStore.refreshTokens">Refresh Token</v-btn>
                <v-btn class="ma-1" @click="keycloakStore.logout">Logout</v-btn>
              </div>
            </template>
          </template>
          <v-card-text class="overflow-x-auto">
            <pre>{{ keycloakStore.tokens }}</pre>
            <!-- <pre>{{ route }}</pre> -->
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6">
        <v-card>
          <v-overlay v-model="isOverlayVisible" class="align-center justify-center bg-white" contained opacity="0.2" />
          <template #title>
            Access Token
            <v-btn class="ma-2" size="small" color="warning" @click="keycloakStore.revokeAccessToken()" v-if="keycloakStore.isActive">Revoke</v-btn>
          </template>
          <template #append v-if="keycloakStore.isActive">
            <span :class="keycloakStore.accessTokenValid ? 'text-success' : 'text-warning'">{{ formatDistanceToNow(keycloakStore.accessClaims.exp * 1000, { addSuffix: true }) }}</span>
          </template>
          <v-card-text class="overflow-x-auto">
            <pre>{{ keycloakStore.accessClaims }}</pre>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6">
        <v-card>
          <v-overlay v-model="isOverlayVisible" class="align-center justify-center bg-white" contained opacity="0.2" />
          <template #title>
            Refresh Token
            <v-btn class="ma-2" size="small" color="warning" @click="keycloakStore.revokeRefreshToken()" v-if="keycloakStore.isActive">Revoke</v-btn>
          </template>
          <template #append v-if="keycloakStore.isActive">
            <span :class="keycloakStore.refreshTokenValid ? 'text-success' : 'text-warning'">
              {{ keycloakStore.refreshClaims.typ === 'Offline' ? 'Never' : formatDistanceToNow(keycloakStore.refreshClaims.exp * 1000, { addSuffix: true }) }}
            </span>
          </template>
          <v-card-text class="overflow-x-auto">
            <pre>{{ keycloakStore.refreshClaims }}</pre>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-switch v-model="isOverlayVisible" />
  </v-container>
</template>

<script>
export default {
  name: 'ViewKeycloak',
};
</script>
