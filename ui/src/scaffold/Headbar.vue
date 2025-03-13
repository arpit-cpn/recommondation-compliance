<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import useKeycloakStore from '../stores/keycloak';
import useNexusStore from '../stores/nexus';
import { useTheme } from 'vuetify';

const theme = useTheme();
const keycloakStore = useKeycloakStore();
const nexusStore = useNexusStore();

const route = useRoute();
const router = useRouter();

const drawer = ref(false);
const about = ref({});

const apps = ref([{
  title: 'Alert Manager',
  icon: 'mdi-car-brake-alert',
  href: 'https://alert.dev.cpnet.ai',
}]);

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark';
};

onMounted(async () => {
  about.value = await fetch('api/tfnexus/v1/about').then(r => r.json());
  if (route?.query?.sso) {
    keycloakStore.login();
  }
});

const switchOrg = (org) => {
  nexusStore.currentOrg = org;
  if (route.name == 'dashboardView') {
    router.push({ name: 'dashboards', params: { org } });
  } else if (['dashboard', 'chartdesigner', 'swapable'].includes(route.name)) {
    router.push({ name: 'dashboard', params: { org } });
  } else {
    router.push({ params: { org } });
  }
};

</script>

<template>
  <v-app-bar>
    <v-app-bar-title style="margin-inline-start: 4px;">
      <div class="d-flex justify-start pl-0">
        <v-app-bar-nav-icon class="align-self-center" @click="drawer = !drawer" v-if="keycloakStore.isActive" />
        <a href="/">
          <img :src="theme.global.current.value.dark ? '/White_Color_Logo.png' : '/Dark_Color_Logo.png'" height="32" position="left" class="me-auto mt-2">
        </a>
      </div>
    </v-app-bar-title>
    <template #append>
      <template v-if="keycloakStore.isActive">
        <v-btn>
          {{ route.params.org }}
          <v-menu activator="parent" v-if="nexusStore.orgs.length > 1">
            <v-list>
              <v-list-item v-for="org in nexusStore.orgs" :key="org.id" @click="switchOrg(org.code)" :title="org.name" :value="org.code" />
            </v-list>
          </v-menu>
        </v-btn>
        <v-btn icon="mdi-view-dashboard" variant="plain" :to="{ name: 'dashboard' }" title="Dashboard" />
        <v-dialog width="auto" location-strategy="connected" offset="80 -120" opacity="0">
          <template #activator="{ props: activatorProps }">
            <v-btn icon="mdi-apps" v-bind="activatorProps" variant="plain" />
          </template>
          <template #default="{ isActive }">
            <v-card prepend-icon="mdi-apps" title="Apps" density="compact" flat>
              <template #append>
                <v-btn icon="mdi-close" @click="isActive.value = false" variant="plain" />
              </template>
              <template #text>
                <v-list :lines="false" density="compact" nav>
                  <v-list-item v-for="(item, i) in apps" :key="i" :prepend-icon="item.icon" :title="item.title" tag="a" :href="`${item.href}/#?sso=1`" class="pa-2" />
                </v-list>
              </template>
            </v-card>
          </template>
        </v-dialog>
        <v-btn
          :icon="theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          variant="plain"
          @click="toggleTheme"
          :title="theme.global.current.value.dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        />
        <v-btn class="text-none mr-2">
          <template #prepend>
            <v-icon icon="mdi-account" />
          </template>
          {{ keycloakStore.accessClaims.preferred_username }}
          <v-menu activator="parent">
            <v-list>
              <v-list-item :title="about?.version" />
              <v-list-item title="Logout" @click="keycloakStore.logout">
                <template #append>
                  <v-btn icon="mdi-logout" size="small" variant="text" />
                </template>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-btn>
      </template>
      <v-btn class="text-none" @click="keycloakStore.login" v-else>
        <template #prepend>
          <v-icon icon="mdi-account" />
        </template>
        Login
      </v-btn>
    </template>
  </v-app-bar>

  <!-- Navigation Drawer -->
  <v-navigation-drawer v-model="drawer" temporary>
    <v-list>
      <v-list-item title="Home" prepend-icon="mdi-home" :to="{ name: 'home' }" :active="route.name === 'home'" />
      <v-list-item title="Dashboard" prepend-icon="mdi-view-dashboard" :to="{ name: 'dashboard' }" :active="route.name === 'dashboard'" />
    </v-list>
  </v-navigation-drawer>

  <!-- <pre>{{ nexusStore }}</pre> -->
  <!-- <pre>{{ keycloakStore }}</pre> -->
</template>

<script>
export default {
  name: 'ScaffoldHeadbar',
};
</script>