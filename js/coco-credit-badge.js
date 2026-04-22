/**
 * CocoCreditBadge — Shows credit balance or "Sign In" in the page header.
 * Auto-inserts into the first <header> element found.
 */
var CocoCreditBadge = {
  _injected: false,

  _t: {
    sign_in:   { en: 'Sign In', fr: 'Connexion', es: 'Entrar' },
    credits:   { en: 'credits', fr: 'crédits', es: 'créditos' },
    my_account:{ en: 'My Account', fr: 'Mon compte', es: 'Mi cuenta' },
    sign_out:  { en: 'Sign Out', fr: 'Déconnexion', es: 'Cerrar sesión' },
    pricing:   { en: 'Pricing', fr: 'Tarifs', es: 'Precios' },
  },

  _lang: function() {
    var el = document.documentElement;
    if (el.lang === 'fr' || document.body.classList.contains('fr')) return 'fr';
    if (el.lang === 'es' || document.body.classList.contains('es')) return 'es';
    return 'en';
  },

  _txt: function(key) {
    var lang = this._lang();
    return (this._t[key] && this._t[key][lang]) || this._t[key].en || key;
  },

  _injectStyle: function() {
    if (this._injected) return;
    this._injected = true;
    var style = document.createElement('style');
    style.textContent = [
      '.coco-badge{position:fixed;top:12px;right:12px;z-index:99998;font-family:system-ui,-apple-system,sans-serif;font-size:14px}',
      '.coco-badge-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;background:rgba(255,255,255,.95);border:1px solid #e5e7eb;border-radius:20px;cursor:pointer;font-weight:600;color:#1a1a2e;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.08);transition:all .15s;backdrop-filter:blur(8px)}',
      '.coco-badge-btn:hover{box-shadow:0 4px 16px rgba(0,0,0,.12);border-color:#7c3aed}',
      '.coco-badge-credits{background:#7c3aed;color:#fff;padding:2px 8px;border-radius:12px;font-size:.85em;font-weight:700}',
      '.coco-badge-avatar{width:24px;height:24px;border-radius:50%;background:#7c3aed;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:.75em;font-weight:700}',
      '.coco-badge-menu{position:absolute;top:100%;right:0;margin-top:6px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.12);min-width:160px;display:none;overflow:hidden}',
      '.coco-badge-menu.open{display:block}',
      '.coco-badge-menu a{display:block;padding:10px 16px;color:#1a1a2e;text-decoration:none;font-size:.9em;transition:background .1s}',
      '.coco-badge-menu a:hover{background:#f3f4f6}',
      '.coco-badge-menu hr{margin:0;border:none;border-top:1px solid #e5e7eb}',
    ].join('\n');
    document.head.appendChild(style);
  },

  render: function() {
    this._injectStyle();

    var existing = document.getElementById('cocoBadge');
    if (existing) existing.remove();

    var container = document.createElement('div');
    container.className = 'coco-badge';
    container.id = 'cocoBadge';

    if (CocoAuth.isLoggedIn()) {
      var cached = CocoAuth.getCachedUser();
      var initial = (cached && cached.email) ? cached.email[0].toUpperCase() : '?';
      var credits = (cached && cached.credits !== undefined) ? cached.credits : '?';

      container.innerHTML = '<div class="coco-badge-btn" id="cocoBadgeBtn">'
        + '<span class="coco-badge-avatar">' + initial + '</span>'
        + '<span class="coco-badge-credits">' + credits + '</span>'
        + '<span>' + this._txt('credits') + '</span>'
        + '</div>'
        + '<div class="coco-badge-menu" id="cocoBadgeMenu">'
        + '<a href="/pricing/">' + this._txt('pricing') + '</a>'
        + '<hr>'
        + '<a href="#" id="cocoBadgeLogout">' + this._txt('sign_out') + '</a>'
        + '</div>';

      document.body.appendChild(container);

      var btn = document.getElementById('cocoBadgeBtn');
      var menu = document.getElementById('cocoBadgeMenu');
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        menu.classList.toggle('open');
      });
      document.addEventListener('click', function() { menu.classList.remove('open'); });

      document.getElementById('cocoBadgeLogout').addEventListener('click', function(e) {
        e.preventDefault();
        CocoAuth.logout();
        CocoCreditBadge.render();
      });

      // Refresh balance in background
      CocoAuth.getUser().then(function(user) {
        if (user && user.credits !== undefined) {
          var el = container.querySelector('.coco-badge-credits');
          if (el) el.textContent = user.credits;
        }
      });
    } else {
      container.innerHTML = '<div class="coco-badge-btn" id="cocoBadgeSignIn">'
        + '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
        + '<span>' + this._txt('sign_in') + '</span>'
        + '</div>';

      document.body.appendChild(container);

      document.getElementById('cocoBadgeSignIn').addEventListener('click', function() {
        showAuthModal(function() { CocoCreditBadge.render(); });
      });
    }
  },

  updateCredits: function(amount) {
    var el = document.querySelector('.coco-badge-credits');
    if (el) el.textContent = amount;
  }
};

// Auto-render on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() { CocoCreditBadge.render(); });
} else {
  CocoCreditBadge.render();
}
