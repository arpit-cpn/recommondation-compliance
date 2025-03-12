import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { createRouter, createWebHashHistory } from 'vue-router';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';
import { aliases, mdi } from 'vuetify/iconsets/mdi';
import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';
import "@fontsource/comfortaa"; // Defaults to weight 400
import "@fontsource/archivo"; // Defaults to weight 400

import App from './App.vue';

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'dark',
  },
});

const app = createApp(App);
app.use(vuetify);

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
app.use(pinia);

const router = createRouter({
  history: createWebHashHistory(),
  routes: [{
    name: 'home',
    path: '/home',
    component: () => import('./views/Home.vue'),
  }, {
    name: 'keycloak',
    path: '/keycloak',
    component: () => import('./views/Keycloak.vue'),
  }, {
    name: 'dashboard',
    path: '/dashboard',
    component: () => import('./views/Dashboard.vue'),
  }, {
    path: '/',
    redirect: { name: 'dashboard' },
  }],
});

app.use(router);

app.mount('#app');
