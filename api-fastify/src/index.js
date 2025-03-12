import pino from 'pino';
import config from 'config';
import Fastify from 'fastify';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import FastifyAutoload from '@fastify/autoload';
import FastifySensible from '@fastify/sensible';
import { rm } from 'node:fs/promises';
import FileStreamRotator from 'file-stream-rotator';

const initApp = async () => {

  await rm(join(dirname(config.get('logger.rotator.filename')), config.get('logger.rotator.symlink_name')), { force: true });
  const loggerInstance = pino({
    level: config.get('logger.level'),
  }, pino.multistream([{
    level: 'debug',
    stream: FileStreamRotator.getStream({ ...config.get('logger.rotator') }),
  }, {
    level: 'debug',
    stream: process.stdout,
  }]));

  const app = Fastify({ loggerInstance });

  await app.register(FastifySensible);

  app.register(FastifyAutoload, {
    dir: join(dirname(fileURLToPath(import.meta.url)), 'auth'),
    options: { prefix: '/auth' },
    routeParams: true,
  });

  app.register(FastifyAutoload, {
    dir: join(dirname(fileURLToPath(import.meta.url)), 'api'),
    options: { prefix: '/api' },
    routeParams: true,
    autoHooks: true,
  });

  return Promise.resolve(app);
};

if (['development', 'production'].includes(process.env.NODE_ENV)) {
  const server = await initApp();
  server.listen({ ...config.get('server') }, (err) => {
    if (err) {
      server.log.error(err);
    } else {
      server.log.info(config.get('server'), 'server started');
    }
  });
}
