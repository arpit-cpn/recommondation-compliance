import { createRouter, createWebHashHistory } from 'vue-router';
import useKeycloakStore from './stores/keycloak';
import useNexusStore from './stores/nexus';

const routes = [
  {
    path: '/',
    redirect: '/home',
  },
  {
    name: 'home',
    path: '/home',
    component: () => import('./views/Home.vue'),
    meta: { isPublic: true },
  }, {
    name: 'keycloak',
    path: '/keycloak',
    component: () => import('./views/Keycloak.vue'),
    meta: { isPublic: true },
  }, {
    name: 'dashboard',
    path: '/dashboard',
    component: () => import('./views/Dashboard.vue'),
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeResolve(async (to, from, next) => {
  const keycloakStore = useKeycloakStore();
  const nexusStore = useNexusStore();

  // Always allow public routes
  if (to.meta.isPublic) {
    return next();
  }

  // Check authentication for protected routes
  if (!keycloakStore.isActive) {
    console.log('User not authenticated, redirecting to home');
    return next({ name: 'home' });
  }

  // Check organization access if org param exists
  if (to.params.org && !nexusStore.isOrgGranted(to.params.org)) {
    console.log('Organization access denied');
    return next({ name: 'home' });
  }

  // Check role-based access
  if (to.meta.role && !keycloakStore.hasRole(to.meta.role)) {
    console.log('Role access denied');
    return next({ name: 'home' });
  }

  // If all checks pass, proceed
  next();
});

export default router;
