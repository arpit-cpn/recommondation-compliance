import os from 'os';
import { readFile } from 'node:fs/promises';
import { createReadStream, existsSync } from 'node:fs';

export default async (app) => {
  const startAt = Date.now();
  const { name, version, build, isReleased } = await readFile('package.json').then(JSON.parse);

  app.get('/about', () => ({
    result: {
      name,
      startAt,
      version,
      build,
      isReleased,
      hostname: os.hostname(),
    },
  }));

  app.get('/releases', (request, reply) => {
    const stream = createReadStream('RELEASES.md');
    reply.type('text/markdown').send(stream);
  });

  app.get('/apps', (request, reply) => {
    const pth = '../usr/apps.json';
    if (existsSync(pth)) {
      const stream = createReadStream(pth);
      reply.type('application/json').send(stream);
    } else {
      reply.send([]);
    }
  });
};
