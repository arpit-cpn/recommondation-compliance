require('dotenv-flow').config();

module.exports = {
  server: {
    port: process.env.PORT,
    host: '::',
  },
  logger: {
    level: 'debug',
    rotator: {
      filename: '../usr/production-logs/production-%DATE%.log',
      frequency: 'custom',
      date_format: 'YYYY-MM-DD',
      max_logs: '14d',
      utc: true,
      symlink_name: 'current.log',
      create_symlink: true,
      verbose: true,
      audit_file: '../usr/production-logs/audit.json',
    },
  },
  keycloak: {
    client: {
      id: process.env.KEYCLOAK_CLIENT_ID,
      secret: process.env.KEYCLOAK_CLIENT_SECRET,
    },
    issuer: `${process.env.KEYCLOAK_OPENID_HOST}/realms/${process.env.KEYCLOAK_OPENID_REALM}`,
    urls: {
      callback: `${process.env.URL_BACKEND}/auth/keycloak/callback`,
      callbackRedirect: `${process.env.URL_FRONTEND}/#/keycloak`,
    },
    scope: process.env.KEYCLOAK_OPENID_SCOPE.split(','),
  },
};
