import _ from 'lodash';
import config from 'config';
import jwkToPem from 'jwk-to-pem';
import FastifyJwt from '@fastify/jwt';
import TTLCache from '@isaacs/ttlcache';

export default async (app) => {

  const urlOpenidConfiguration = `${config.get('keycloak.issuer')}/.well-known/openid-configuration`;
  const { jwks_uri } = await fetch(urlOpenidConfiguration).then(r => r.json());

  const jwtPems = new TTLCache({ ttl: 1000 * 60 * 60 });

  app.register(FastifyJwt, {
    decode: { complete: true },
    secret: async (request, token) => {
      if (!jwtPems.has(token.header.kid)) {
        const { keys } = await fetch(jwks_uri).then((r) => r.json());
        keys.forEach(({ kid, ...v }) => {
          jwtPems.set(kid, jwkToPem(v));
        });
      }
      if (!jwtPems.has(token.header.kid)) {
        throw new Error('invalid kid');
      }
      return Promise.resolve(jwtPems.get(token.header.kid));
    },
    verify: {
      allowedIss: config.get('keycloak.issuer'),
      cache: true,
    },
    trusted(request, decodedToken) {
      return decodedToken.aur === config.get('keycloak.client.id') ||
        decodedToken.azp === config.get('keycloak.client.id');
    },
  });

  app.decorate('authenticate', async (request, reply) => {
    try {
      await request.jwtVerify();
    } catch (err) {
      reply.unauthorized(err.message);
    }
  });

  app.decorate('claimContainRequired', (path, target) => (request, reply, done) => {
    if (_.get(request.user, path, []).includes(target)) {
      done();
    } else {
      reply.forbidden();
    }
  });
};
