/**
 * CocoAuth — Shared auth + credit utilities for all Coco the Axolotl pages.
 * Stores JWT tokens in localStorage. Handles auto-refresh.
 */
var COCO_API = 'https://mosaic-api.fly.dev';

var CocoAuth = {
  // ── Token management ──────────────────────────────────────────────────

  getToken: function() { return localStorage.getItem('coco_access_token'); },
  getRefresh: function() { return localStorage.getItem('coco_refresh_token'); },
  isLoggedIn: function() { return !!this.getToken(); },

  _saveTokens: function(data) {
    if (data.access_token) localStorage.setItem('coco_access_token', data.access_token);
    if (data.refresh_token) localStorage.setItem('coco_refresh_token', data.refresh_token);
  },

  logout: function() {
    var rt = this.getRefresh();
    if (rt) {
      fetch(COCO_API + '/api/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt })
      }).catch(function() {});
    }
    localStorage.removeItem('coco_access_token');
    localStorage.removeItem('coco_refresh_token');
    localStorage.removeItem('coco_user');
    if (typeof CocoCreditBadge !== 'undefined') CocoCreditBadge.render();
  },

  // ── Auth API calls ────────────────────────────────────────────────────

  signup: async function(email, password, displayName, lang) {
    var resp = await fetch(COCO_API + '/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        password: password,
        display_name: displayName || '',
        lang: lang || 'en'
      })
    });
    var data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Signup failed');
    this._saveTokens(data);
    localStorage.setItem('coco_user', JSON.stringify(data));
    return data;
  },

  login: async function(email, password) {
    var resp = await fetch(COCO_API + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    });
    var data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Login failed');
    this._saveTokens(data);
    localStorage.setItem('coco_user', JSON.stringify(data));
    return data;
  },

  refreshToken: async function() {
    var rt = this.getRefresh();
    if (!rt) return false;
    try {
      var resp = await fetch(COCO_API + '/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt })
      });
      if (!resp.ok) { this.logout(); return false; }
      var data = await resp.json();
      this._saveTokens(data);
      return true;
    } catch (e) {
      this.logout();
      return false;
    }
  },

  // ── Authenticated fetch helper ────────────────────────────────────────

  _authFetch: async function(url, options) {
    options = options || {};
    options.headers = options.headers || {};
    var token = this.getToken();
    if (token) options.headers['Authorization'] = 'Bearer ' + token;

    var resp = await fetch(url, options);
    if (resp.status === 401 && token) {
      var refreshed = await this.refreshToken();
      if (refreshed) {
        options.headers['Authorization'] = 'Bearer ' + this.getToken();
        resp = await fetch(url, options);
      }
    }
    return resp;
  },

  // ── Get current user profile ──────────────────────────────────────────

  getUser: async function() {
    if (!this.isLoggedIn()) return null;
    var resp = await this._authFetch(COCO_API + '/api/auth/me');
    if (!resp.ok) return null;
    var data = await resp.json();
    localStorage.setItem('coco_user', JSON.stringify(data));
    return data;
  },

  getCachedUser: function() {
    try { return JSON.parse(localStorage.getItem('coco_user')); }
    catch (e) { return null; }
  },

  // ── Credits ───────────────────────────────────────────────────────────

  consumeCredit: async function(feature, variant) {
    if (!this.isLoggedIn()) return { ok: false, reason: 'not_logged_in' };
    var resp = await this._authFetch(COCO_API + '/api/credits/consume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feature: feature, variant: variant || '' })
    });
    if (resp.status === 401) return { ok: false, reason: 'not_logged_in' };
    if (resp.status === 402) {
      var errData = await resp.json();
      return { ok: false, reason: 'no_credits', data: errData };
    }
    if (!resp.ok) return { ok: false, reason: 'error' };
    var data = await resp.json();
    // Update cached user credits
    var cached = this.getCachedUser();
    if (cached) { cached.credits = data.remaining; localStorage.setItem('coco_user', JSON.stringify(cached)); }
    return { ok: true, data: data };
  },

  getBalance: async function() {
    if (!this.isLoggedIn()) return null;
    var resp = await this._authFetch(COCO_API + '/api/credits/balance');
    if (!resp.ok) return null;
    return await resp.json();
  },

  // ── Password reset ────────────────────────────────────────────────────

  forgotPassword: async function(email, lang) {
    var resp = await fetch(COCO_API + '/api/auth/forgot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, lang: lang || 'en' })
    });
    return resp.ok;
  },

  resetPassword: async function(token, newPassword) {
    var resp = await fetch(COCO_API + '/api/auth/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token, password: newPassword })
    });
    return resp.ok;
  }
};

// ── Free download soft gate (for name generators) ────────────────────────

var FREE_DOWNLOADS = 1;

function canDownloadFree() {
  var used = parseInt(localStorage.getItem('coco_name_dl_count') || '0', 10);
  return used < FREE_DOWNLOADS;
}

function recordFreeDownload() {
  var used = parseInt(localStorage.getItem('coco_name_dl_count') || '0', 10);
  localStorage.setItem('coco_name_dl_count', String(used + 1));
}
