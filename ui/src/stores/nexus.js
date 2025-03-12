import _ from 'lodash';
import { defineStore } from 'pinia';
import Fetcher from '../Fetcher';
const http = new Fetcher('api/tfnexus/');

export default defineStore('orgs', {
  state: () => ({
    orgs: [],
    currentOrg: '_blank',
    loading: false,
    error: null,
  }),
  actions: {
    async fetchOrgs(jwt) {
      this.orgs = await http.get('v1/tenants', {
        headers: { Authorization: `Bearer ${jwt}` },
      }).then((lst) => lst.map((d) => ({ code: d.alias.toLowerCase(), ...d })));
      if (_.findIndex(this.orgs, { code: this.currentOrg }) === -1) {
        this.currentOrg = this.orgs[0].code;
      }
      console.log(this.orgs);
    },
    isOrgGranted(code) {
      return _.findIndex(this.orgs, { code }) > -1;
    },
    getTenantId(code) {
      return _.chain(this.orgs).find({ code }).get('id').value();
    },
  },
  persist: true,
});
