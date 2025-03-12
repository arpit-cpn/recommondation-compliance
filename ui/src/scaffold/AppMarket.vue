<script setup>
import { onMounted, ref } from 'vue';
const apps = ref([]);

onMounted(async () => {
  apps.value = await fetch('/api/apps').then(r => r.json());
});

</script>

<template>
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
</template>
