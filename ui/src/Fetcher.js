import _ from 'lodash';

export default class Fetcher {
  constructor(baseURL = 'api/', onPreRequest = () => Promise.resolve(), emitter = null) {
    this.baseURL = baseURL;
    this.timeout = 30000;
    this.onPreRequest = onPreRequest;
    this.emitter = emitter;
  }

  http(url, {
    query, timeout: tot, muted = false, ...options
  }) {
    return new Promise((resolve, reject) => {
      const controller = new AbortController();

      _.set(options, 'headers["Cache-Control"]', 'no-cache');
      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
        _.set(options, 'headers["Content-Type"]', 'application/json');
      }

      const searchString = query ? `?${new URLSearchParams(query).toString()}` : '';

      let resource = `${url}${searchString}`;
      if (!(resource.match(/^https?:\/\//) || resource.startsWith('/'))) {
        resource = `${this.baseURL}${resource}`;
      }

      this.onPreRequest(options).then(() => {
        const timeoutId = setTimeout(() => controller.abort(), tot || this.timeout);

        fetch(resource, { ...options, signal: controller.signal }).then((response) => {
          if (response.ok) {
            if (response.status === 204) {
              resolve();
            } else if (response.headers.get('content-type').startsWith('application/json')) {
              response.json().then(resolve).catch(reject);
            } else {
              resolve(response);
            }
          } else if (muted) {
            const error = new Error(response.statusText);
            error.status = response.status;
            throw error;
          } else {
            response.json().then((data) => {
              console.log(data);
              if (this.emitter) {
                this.emitter.emit('message', { color: 'error', text: _.map(data?.detail, 'msg').join('\n') || data.error || data.statusCode });
              }
              const error = new Error(response.statusText);
              error.status = response.status;
              reject(error);
            });
          }
          clearTimeout(timeoutId);
        }).catch((e) => {
          if (e instanceof (DOMException) && this.emitter) {
            this.emitter.emit('message', { type: 'error', message: 'request timeout' });
          } else {
            reject(e);
          }
        });
      }).catch((e) => {
        reject(e);
      });
    });
  }

  get(url, options) {
    return this.http(url, { ...options, method: 'GET' });
  }

  post(url, data, options) {
    return this.http(url, { ...options, method: 'POST', body: JSON.stringify(data || {}) });
  }

  put(url, data, options) {
    return this.http(url, { ...options, method: 'PUT', body: JSON.stringify(data) });
  }

  patch(url, data, options) {
    return this.http(url, { ...options, method: 'PATCH', body: JSON.stringify(data) });
  }

  delete(url, data, options) {
    return this.http(url, { ...options, method: 'DELETE', body: JSON.stringify(data || {}) });
  }
}
