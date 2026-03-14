/**
 * Universal language switcher for cocotheaxolotl.org
 * Auto-detects current language from URL and renders a fixed top-right toggle.
 * Skip injection if a .lang-toggle already exists on the page.
 */
(function () {
  // Don't add if the page already has a lang toggle
  if (document.querySelector('.lang-toggle')) return;

  var path = window.location.pathname;
  var lang = 'en';
  var basePath = path;

  if (path.indexOf('/fr/') === 0) {
    lang = 'fr';
    basePath = path.slice(3); // /fr/page/ → /page/
  } else if (path.indexOf('/es/') === 0) {
    lang = 'es';
    basePath = path.slice(3); // /es/page/ → /page/
  }

  var enUrl = basePath || '/';
  var frUrl = '/fr' + (basePath || '/');
  var esUrl = '/es' + (basePath || '/');

  // Inject CSS once
  var style = document.createElement('style');
  style.textContent =
    '.ls-toggle{position:fixed;top:12px;right:12px;z-index:9999;display:inline-flex;' +
    'border-radius:32px;overflow:hidden;border:2px solid rgba(255,105,180,.7);' +
    'background:rgba(255,255,255,.85);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);' +
    'box-shadow:0 2px 8px rgba(0,0,0,.15)}' +
    '.ls-btn{padding:5px 14px;font-family:"Baloo 2",system-ui,sans-serif;font-size:.85em;font-weight:800;' +
    'border:none;cursor:pointer;text-decoration:none;color:#c0186a;background:transparent;display:inline-block}' +
    '.ls-btn.ls-active{background:#ff69b4;color:#fff}';
  document.head.appendChild(style);

  // Build toggle HTML
  var div = document.createElement('div');
  div.className = 'ls-toggle';
  div.innerHTML =
    '<a class="ls-btn' + (lang === 'en' ? ' ls-active' : '') + '" href="' + enUrl + '">EN</a>' +
    '<a class="ls-btn' + (lang === 'fr' ? ' ls-active' : '') + '" href="' + frUrl + '">FR</a>' +
    '<a class="ls-btn' + (lang === 'es' ? ' ls-active' : '') + '" href="' + esUrl + '">ES</a>';

  function inject() { document.body.appendChild(div); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
