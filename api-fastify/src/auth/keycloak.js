import _ from 'lodash';
import config from 'config';
import TTLCache from '@isaacs/ttlcache';
import FastifyOauth2 from '@fastify/oauth2';

export default async (app) => {
  const urlOpenidConfiguration = `${config.get('keycloak.issuer')}/.well-known/openid-configuration`;
  const { end_session_endpoint, userinfo_endpoint, token_endpoint, revocation_endpoint } = await fetch(urlOpenidConfiguration).then(r => r.json());
  app.log.info(urlOpenidConfiguration);

  app.register(FastifyOauth2, {
    name: 'keycloak',
    credentials: {
      client: config.get('keycloak.client'),
    },
    discovery: {
      issuer: config.get('keycloak.issuer'),
    },
    startRedirectPath: '/login',
    callbackUri: config.get('keycloak.urls.callback'),
    scope: config.get('keycloak.scope'),
  });

  const tokenCache = new TTLCache({ ttl: 60000 });

  app.get('/callback', async (req, res) => {
    // app.log.info(req.query);
    const { token } = await app.keycloak.getAccessTokenFromAuthorizationCodeFlow(req);
    // app.log.info({ token });
    const { session_state } = token;
    tokenCache.set(session_state, token);
    const search = new URLSearchParams({ session_state });
    res.redirect(`${config.get('keycloak.urls.callbackRedirect')}?${search.toString()}`);
  });

  app.post('/tokens', async (req, res) => {
    res.send(tokenCache.get(req.body.session_state));
    tokenCache.delete(req.body.session_state);
  });

  app.get('/userinfo', (req, res) => {
    fetch(userinfo_endpoint, { headers: _.pick(req.headers, 'authorization') }).then((resp) => {
      res.status(resp.status).type('application/json').send(resp.body);
    });
  });

  app.get('/logout', (req, res) => {
    const url = new URL(end_session_endpoint);
    url.search = new URLSearchParams(req.query).toString();
    res.redirect(url.href);
  });

  app.post('/tokens/refresh', (req, res) => {
    fetch(token_endpoint, {
      method: 'POST',
      body: new URLSearchParams({
        client_id: config.get('keycloak.client.id'),
        client_secret: config.get('keycloak.client.secret'),
        refresh_token: req.body.refresh_token,
        grant_type: 'refresh_token',
      }),
    }).then((resp) => {
      res.status(resp.status).type('application/json').send(resp.body);
    });
  });

  app.post('/tokens/revoke', (req, res) => {
    fetch(revocation_endpoint, {
      method: 'POST',
      body: new URLSearchParams({
        client_id: config.get('keycloak.client.id'),
        client_secret: config.get('keycloak.client.secret'),
        ...req.body,
      }),
    }).then((resp) => {
      res.status(resp.status).type('application/json').send(resp.body);
    });
  });

  app.post('/tokens/exchange', (req, res) => {
    app.log.info({
      client_id: config.get('keycloak.client.id'),
      client_secret: config.get('keycloak.client.secret'),
      grant_type: 'urn:ietf:params:oauth:grant-type:token-exchange',
      subject_token: req.body.access_token,
      audience: 'apidemo',
      // scope: 'openid',
    });
    fetch(token_endpoint, {
      method: 'POST',
      body: new URLSearchParams({
        client_id: config.get('keycloak.client.id'),
        client_secret: config.get('keycloak.client.secret'),
        grant_type: 'urn:ietf:params:oauth:grant-type:token-exchange',
        subject_token: req.body.access_token,
        audience: 'apidemo',
        scope: 'openid',
      }),
    }).then((resp) => {
      res.status(resp.status).type('application/json').send(resp.body);
    });
  });

  app.get('/configurations', async () => {
    const configurations = await fetch(urlOpenidConfiguration).then(r => r.json());
    return {
      client_id: config.get('keycloak.client.id'),
      ...configurations,
    };
  });

};

export const autoPrefix = '/keycloak';
