/**
 * CocoAuthModal — Lightweight login/signup modal.
 * Injects itself into document.body. Supports EN/FR/ES via data-lang.
 */
var CocoAuthModal = {
  _injected: false,
  _callback: null,

  _t: {
    signup_title:   { en: 'Create Account', fr: 'Créer un compte', es: 'Crear cuenta' },
    login_title:    { en: 'Sign In', fr: 'Connexion', es: 'Iniciar sesión' },
    email:          { en: 'Email', fr: 'Email', es: 'Email' },
    password:       { en: 'Password', fr: 'Mot de passe', es: 'Contraseña' },
    name:           { en: 'Name (optional)', fr: 'Nom (optionnel)', es: 'Nombre (opcional)' },
    signup_btn:     { en: 'Sign Up', fr: "S'inscrire", es: 'Registrarse' },
    login_btn:      { en: 'Sign In', fr: 'Connexion', es: 'Entrar' },
    switch_login:   { en: 'Already have an account? Sign In', fr: 'Déjà un compte ? Connexion', es: '¿Ya tienes cuenta? Entrar' },
    switch_signup:  { en: "Don't have an account? Sign Up", fr: "Pas de compte ? S'inscrire", es: '¿No tienes cuenta? Registrarse' },
    forgot:         { en: 'Forgot password?', fr: 'Mot de passe oublié ?', es: '¿Olvidaste tu contraseña?' },
    bonus:          { en: '3 free credits included!', fr: '3 crédits offerts !', es: '¡3 créditos gratis!' },
    forgot_title:   { en: 'Reset Password', fr: 'Réinitialiser', es: 'Restablecer' },
    forgot_btn:     { en: 'Send Reset Link', fr: 'Envoyer le lien', es: 'Enviar enlace' },
    forgot_sent:    { en: 'If an account exists, a reset email has been sent.', fr: 'Si un compte existe, un email a été envoyé.', es: 'Si existe una cuenta, se ha enviado un email.' },
    back_login:     { en: 'Back to Sign In', fr: 'Retour à la connexion', es: 'Volver a iniciar sesión' },
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

  _inject: function() {
    if (this._injected) return;
    this._injected = true;

    var style = document.createElement('style');
    style.textContent = [
      '.coco-auth-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:100000;align-items:center;justify-content:center;font-family:system-ui,-apple-system,sans-serif}',
      '.coco-auth-overlay.active{display:flex}',
      '.coco-auth-box{background:#fff;border-radius:16px;padding:32px 28px;max-width:380px;width:92vw;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.2)}',
      '.coco-auth-box h2{margin:0 0 6px;font-size:1.4em;color:#1a1a2e}',
      '.coco-auth-box .bonus{color:#7c3aed;font-size:.85em;margin:0 0 18px;font-weight:600}',
      '.coco-auth-box input{width:100%;padding:12px 14px;border:2px solid #e5e7eb;border-radius:10px;font-size:1em;margin:0 0 12px;box-sizing:border-box;outline:none;transition:border .15s}',
      '.coco-auth-box input:focus{border-color:#7c3aed}',
      '.coco-auth-box .btn{width:100%;padding:13px;background:#7c3aed;color:#fff;border:none;border-radius:10px;font-size:1.05em;font-weight:700;cursor:pointer;transition:background .15s}',
      '.coco-auth-box .btn:hover{background:#6d28d9}',
      '.coco-auth-box .btn:disabled{opacity:.5;cursor:not-allowed}',
      '.coco-auth-box .switch{text-align:center;margin:14px 0 0;font-size:.9em;color:#6b7280}',
      '.coco-auth-box .switch a{color:#7c3aed;cursor:pointer;text-decoration:none;font-weight:600}',
      '.coco-auth-box .forgot{text-align:right;margin:-6px 0 12px;font-size:.82em}',
      '.coco-auth-box .forgot a{color:#7c3aed;cursor:pointer;text-decoration:none}',
      '.coco-auth-box .error{color:#dc2626;font-size:.85em;margin:0 0 10px;display:none}',
      '.coco-auth-box .close{position:absolute;top:12px;right:16px;background:none;border:none;font-size:1.5em;cursor:pointer;color:#9ca3af;line-height:1}',
      '.coco-auth-box .close:hover{color:#333}',
    ].join('\n');
    document.head.appendChild(style);

    var overlay = document.createElement('div');
    overlay.className = 'coco-auth-overlay';
    overlay.id = 'cocoAuthOverlay';
    overlay.innerHTML = '<div class="coco-auth-box" id="cocoAuthBox"></div>';
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) CocoAuthModal.close();
    });
    document.body.appendChild(overlay);
  },

  _renderSignup: function() {
    var self = this;
    var box = document.getElementById('cocoAuthBox');
    box.innerHTML = '<button class="close" id="camClose">&times;</button>'
      + '<h2>' + this._txt('signup_title') + '</h2>'
      + '<p class="bonus">' + this._txt('bonus') + '</p>'
      + '<div class="error" id="camError"></div>'
      + '<input type="text" id="camName" placeholder="' + this._txt('name') + '">'
      + '<input type="email" id="camEmail" placeholder="' + this._txt('email') + '">'
      + '<input type="password" id="camPass" placeholder="' + this._txt('password') + '">'
      + '<button class="btn" id="camSubmit">' + this._txt('signup_btn') + '</button>'
      + '<div class="switch">' + this._txt('switch_login').replace(/(Sign In|Connexion|Entrar)/, '<a id="camSwitchLogin">$1</a>') + '</div>';

    box.querySelector('#camClose').onclick = function() { self.close(); };
    box.querySelector('#camSwitchLogin').onclick = function() { self._renderLogin(); };
    box.querySelector('#camSubmit').onclick = function() { self._doSignup(); };
    box.querySelector('#camPass').addEventListener('keydown', function(e) { if (e.key === 'Enter') self._doSignup(); });
  },

  _renderLogin: function() {
    var self = this;
    var box = document.getElementById('cocoAuthBox');
    box.innerHTML = '<button class="close" id="camClose">&times;</button>'
      + '<h2>' + this._txt('login_title') + '</h2>'
      + '<div class="error" id="camError"></div>'
      + '<input type="email" id="camEmail" placeholder="' + this._txt('email') + '">'
      + '<input type="password" id="camPass" placeholder="' + this._txt('password') + '">'
      + '<div class="forgot"><a id="camForgot">' + this._txt('forgot') + '</a></div>'
      + '<button class="btn" id="camSubmit">' + this._txt('login_btn') + '</button>'
      + '<div class="switch">' + this._txt('switch_signup').replace(/(Sign Up|S'inscrire|Registrarse)/, '<a id="camSwitchSignup">$1</a>') + '</div>';

    box.querySelector('#camClose').onclick = function() { self.close(); };
    box.querySelector('#camSwitchSignup').onclick = function() { self._renderSignup(); };
    box.querySelector('#camForgot').onclick = function() { self._renderForgot(); };
    box.querySelector('#camSubmit').onclick = function() { self._doLogin(); };
    box.querySelector('#camPass').addEventListener('keydown', function(e) { if (e.key === 'Enter') self._doLogin(); });
  },

  _renderForgot: function() {
    var self = this;
    var box = document.getElementById('cocoAuthBox');
    box.innerHTML = '<button class="close" id="camClose">&times;</button>'
      + '<h2>' + this._txt('forgot_title') + '</h2>'
      + '<div class="error" id="camError"></div>'
      + '<input type="email" id="camEmail" placeholder="' + this._txt('email') + '">'
      + '<button class="btn" id="camSubmit">' + this._txt('forgot_btn') + '</button>'
      + '<div class="switch"><a id="camBackLogin">' + this._txt('back_login') + '</a></div>';

    box.querySelector('#camClose').onclick = function() { self.close(); };
    box.querySelector('#camBackLogin').onclick = function() { self._renderLogin(); };
    box.querySelector('#camSubmit').onclick = async function() {
      var email = box.querySelector('#camEmail').value.trim();
      if (!email) return;
      var btn = box.querySelector('#camSubmit');
      btn.disabled = true;
      await CocoAuth.forgotPassword(email, self._lang());
      btn.textContent = self._txt('forgot_sent');
      btn.disabled = true;
    };
  },

  _showError: function(msg) {
    var el = document.getElementById('camError');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
  },

  _doSignup: async function() {
    var email = document.getElementById('camEmail').value.trim();
    var pass = document.getElementById('camPass').value;
    var name = document.getElementById('camName').value.trim();
    var btn = document.getElementById('camSubmit');
    if (!email || !pass) return;

    btn.disabled = true;
    try {
      var data = await CocoAuth.signup(email, pass, name, this._lang());
      this.close();
      if (typeof CocoCreditBadge !== 'undefined') CocoCreditBadge.render();
      if (this._callback) this._callback(data);
    } catch (e) {
      this._showError(e.message);
      btn.disabled = false;
    }
  },

  _doLogin: async function() {
    var email = document.getElementById('camEmail').value.trim();
    var pass = document.getElementById('camPass').value;
    var btn = document.getElementById('camSubmit');
    if (!email || !pass) return;

    btn.disabled = true;
    try {
      var data = await CocoAuth.login(email, pass);
      this.close();
      if (typeof CocoCreditBadge !== 'undefined') CocoCreditBadge.render();
      if (this._callback) this._callback(data);
    } catch (e) {
      this._showError(e.message);
      btn.disabled = false;
    }
  },

  // ── Public API ────────────────────────────────────────────────────────

  open: function(mode, callback) {
    this._inject();
    this._callback = callback || null;
    if (mode === 'login') this._renderLogin();
    else this._renderSignup();
    document.getElementById('cocoAuthOverlay').classList.add('active');
  },

  close: function() {
    var overlay = document.getElementById('cocoAuthOverlay');
    if (overlay) overlay.classList.remove('active');
    this._callback = null;
  }
};

// Convenience globals
function showAuthModal(callback) { CocoAuthModal.open('signup', callback); }
function showLoginModal(callback) { CocoAuthModal.open('login', callback); }
