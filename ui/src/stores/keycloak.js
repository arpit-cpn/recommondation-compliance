import _ from 'lodash';
import AsyncLock from 'async-lock';
import { defineStore } from 'pinia';
import useNexusStore from './nexus';

const lock = new AsyncLock();

export default defineStore('keycloak', {
  state: () => ({
    tokens: {},
    userinfo: {},
    urlSessionIframe: null,
    urlSessionIframeOrigin: null,
    clientId: '',
    sessionStateLast: null,
  }),
  getters: {
    isActive(state) {
      return !!state.tokens?.access_token;
    },
    accessClaims(state) {
      if (state.tokens.access_token) {
        return JSON.parse(atob(state.tokens.access_token.split('.')[1]));
      }
      return null;
    },
    refreshClaims(state) {
      if (state.tokens.access_token) {
        return JSON.parse(atob(state.tokens.refresh_token.split('.')[1]));
      }
      return null;
    },
    idClaims(state) {
      if (state.tokens.access_token) {
        return JSON.parse(atob(state.tokens.id_token.split('.')[1]));
      }
      return null;
    },
    accessTokenValid() {
      return this.accessClaims && this.accessClaims.exp * 1000 > Date.now();
    },
    refreshTokenValid() {
      return this.refreshClaims.typ === 'Offline' ? true : this.refreshClaims && this.refreshClaims.exp * 1000 > Date.now();
    },
  },
  actions: {
    fetchTokens(session_state) {
      return fetch('/auth/keycloak/tokens', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_state }),
      }).then((r) => r.json()).then((d) => {
        this.tokens = d;
        useNexusStore().fetchOrgs(this.tokens.access_token);

      });
    },
    refreshTokens() {
      return fetch('/auth/keycloak/tokens/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(_.pick(this.tokens, 'refresh_token')),
      }).then((r) => {
        if (r.ok) {
          return r.json().then((d) => {
            this.tokens = d;
          });
        }
        // return this.logout();
        return this.login();
      });
    },
    exchangeToken() {
      return fetch('/auth/keycloak/tokens/exchange', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(_.pick(this.tokens, 'access_token')),
      });
    },
    fetchUserinfo() {
      fetch('/auth/keycloak/userinfo', {
        headers: {
          Authorization: `Bearer ${this.tokens.access_token}`,
        },
      }).then((r) => {
        if (r.ok) {
          r.json().then((d) => {
            this.userinfo = d;
          });
        }
      });
    },
    async logout() {
      // await this.revokeRefreshToken();
      const url = new URL(window.location.origin);
      url.pathname = '/auth/keycloak/logout';
      url.search = new URLSearchParams({
        post_logout_redirect_uri: window.location.origin,
        id_token_hint: this.tokens.id_token,
      });
      this.tokens = {};
      this.userinfo = {};
      window.location.replace(url.href);
    },
    revokeAccessToken() {
      return fetch('/auth/keycloak/tokens/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: this.tokens.access_token,
          token_type_hint: 'access_token',
        }),
      });
    },
    revokeRefreshToken() {
      return fetch('/auth/keycloak/tokens/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: this.tokens.refresh_token,
          token_type_hint: 'refresh_token',
        }),
      });
    },
    async ensureAccessToken() {
      return lock.acquire('ensureAccessToken', () => {
        if (Date.now() > this.accessClaims.exp * 1000) {
          return this.refreshTokens();
        }
        return Promise.resolve();
      });
    },
    login() {
      window.location.replace('/auth/keycloak/login');
    },
    hasRole(role) {
      if (this.accessClaims?.realm_access) {
        return this.accessClaims.realm_access.roles.includes(role);
      }
      return false;
    },
    checkSession() {
      document.getElementById('keycloak-session-iframe').contentWindow.postMessage(`${this.clientId} ${this.tokens.session_state}`, this.urlSessionIframeOrigin);
    },
    messageHandler(e) {
      if (e.source !== document.getElementById('keycloak-session-iframe').contentWindow) {
        return;
      }

      console.log(`${this.isActive}: ${this.sessionStateLast} -> ${e.data}`);
      if (this.isActive && e.data === 'error') {
        this.login();
      }

      if (e.data === 'changed') {
        if (this.sessionStateLast === 'unchanged') {
          console.log('logout from outside'); // works
          this.logout();
        }
      }

      this.sessionStateLast = e.data;

      setTimeout(() => {
        this.checkSession();
      }, 5000);
    },
    init() {
      this.sessionStateLast = null;
      document.getElementById('keycloak-session-iframe').onload = () => {
        console.log('op loaded');
        window.addEventListener('message', this.messageHandler, false);
        this.checkSession();
      };
      return fetch('/auth/keycloak/configurations').then(r => r.json()).then(({
        check_session_iframe,
        client_id,
      }) => {
        this.urlSessionIframe = check_session_iframe;
        this.urlSessionIframeOrigin = new URL(check_session_iframe).origin;
        this.clientId = client_id;
      });
    },
    destroy() {
      window.removeEventListener('message', this.messageHandler, false);
    },
  },
  persist: true,
});
