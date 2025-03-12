Create a realm admin user
---

1. On `${KEYCLOAK_HOST}/admin/master/console`, login with master Admin account,

  1.1 create a keycloak realm `${KEYCLOAK_REALM}`

  1.2 in `Configure / Identity providers`, Add identity provider like Microsoft.

2. On `${KEYCLOAK_HOST}/realms/${KEYCLOAK_REALM}/account`, login with a manager account `${KEYCLOAK_MANAGER}`.

  So a new user is created in the user list

3. On `${KEYCLOAK_HOST}/admin/master/console`, login with Admin account,

  3.1 Switch to `${KEYCLOAK_REALM}`

  3.2 In `Users / ${KEYCLOAK_MANAGER} / Role mapping`, Assign `realm-admin` to `${KEYCLOAK_MANAGER}`

4. Login `${KEYCLOAK_HOST}/admin/${KEYCLOAK_REALM}/console` with your own Admin account, without involving the master admin account or the master realm.

Create a APP client in Keycloak
---

  * Client ID: `${KEYCLOAK_CLIENT_ID}`
  * Client authentication: `ON`
  * Authentication flow: `Standard flow`
  * Valid redirect URIs: `${URL_BACKEND}/auth/keycloak/callback`
  * Valid post logout redirect URIs: `${URL_FRONTEND}/*`
  * Web origins: `${URL_FRONTEND}`

ENV Setup
---

All Keycloak related ENV variables in `api-fastapi/.env` or `api-fastify/.env` are referenced above.

Enhanced Tracking Protection
---

On local development, where frontend is served locally on localhost, Browsers like Firefox would block 3rd-party cookies, then SSO would failed to load. It would result in strange behavior in the login process.

It can be turned off in the `Shield menu` next to the broweser URL bar.
