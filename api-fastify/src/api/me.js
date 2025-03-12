export default async (app) => {
  app.addHook('onRequest', app.authenticate);

  app.get('', ({ user }) => ({
    user,
  }));

  app.get('/roles', {
    onRequest: [
      app.claimContainRequired('realm_access.roles', 'uma_authorization'),
    ],
  }, ({ user }) => ({
    user,
  }));

};

export const autoPrefix = '/me';
