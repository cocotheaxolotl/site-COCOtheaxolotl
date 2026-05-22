/* email-gate.js - capture email before letting anonymous users download
   Behavior:
   - If user is logged in (us_tokens) OR has already given email (us_email_given) -> no gate
   - Otherwise, intercept clicks on elements marked [data-email-gate]
   - Show a modal asking name + email, POST to /api/subscribe, then proceed with the original action
   Storage flag: localStorage 'us_email_given' = '1'
*/
(function () {
  if (window.__usEmailGateLoaded) return;
  window.__usEmailGateLoaded = true;

  var GATE_KEY = 'us_email_given';

  function isLoggedIn() {
    try {
      var t = JSON.parse(localStorage.getItem('us_tokens'));
      return !!(t && t.access_token);
    } catch (e) { return false; }
  }
  function hasGivenEmail() {
    return localStorage.getItem(GATE_KEY) === '1';
  }
  function markEmailGiven() {
    try { localStorage.setItem(GATE_KEY, '1'); } catch (e) {}
  }
  function shouldGate() {
    return !(isLoggedIn() || hasGivenEmail());
  }

  function getLang() {
    return (document.documentElement.lang || 'en').slice(0, 2);
  }

  var T = {
    en: {
      title: 'Before you download...',
      sub: 'Drop your email to grab the file <strong>+ free Coco coloring pages every month</strong>. No spam, ever.',
      name: 'First name (optional)',
      email: 'Your email',
      btn: 'Get it & download',
      loading: 'Sending...',
      err: 'Invalid email. Try again.',
      errNet: 'Network issue. Try again.',
      close: 'Close'
    },
    fr: {
      title: 'Avant de télécharger...',
      sub: 'Laisse ton email pour recevoir le fichier <strong>+ des coloriages Coco gratuits chaque mois</strong>. Jamais de spam.',
      name: 'Prénom (facultatif)',
      email: 'Ton email',
      btn: 'Recevoir et télécharger',
      loading: 'Envoi...',
      err: 'Email invalide. Réessaie.',
      errNet: 'Problème réseau. Réessaie.',
      close: 'Fermer'
    },
    es: {
      title: 'Antes de descargar...',
      sub: 'Deja tu email para recibir el archivo <strong>+ dibujos de Coco gratis cada mes</strong>. Sin spam.',
      name: 'Nombre (opcional)',
      email: 'Tu email',
      btn: 'Recibir y descargar',
      loading: 'Enviando...',
      err: 'Email inválido. Inténtalo de nuevo.',
      errNet: 'Error de red. Reintenta.',
      close: 'Cerrar'
    },
    it: {
      title: 'Prima di scaricare...',
      sub: 'Lascia la tua email per ricevere il file <strong>+ disegni di Coco gratuiti ogni mese</strong>. Niente spam.',
      name: 'Nome (facoltativo)',
      email: 'La tua email',
      btn: 'Ricevi e scarica',
      loading: 'Invio...',
      err: 'Email non valida. Riprova.',
      errNet: 'Problema di rete. Riprova.',
      close: 'Chiudi'
    },
    ja: {
      title: '?????????...',
      sub: '???????????????????????? <strong>+ Coco????????????</strong>?????????????',
      name: '??????',
      email: '???????',
      btn: '???????????',
      loading: '???...',
      err: '?????????????????????????????',
      errNet: '????????????????????',
      close: '???'
    },
    jp: {
      title: '?????????...',
      sub: '???????????????????????? <strong>+ Coco????????????</strong>?????????????',
      name: '??????',
      email: '???????',
      btn: '???????????',
      loading: '???...',
      err: '?????????????????????????????',
      errNet: '????????????????????',
      close: '???'
    },
    de: {
      title: 'Bevor du herunterlädst…',
      sub: 'Gib deine E-Mail an, um die Datei zu erhalten <strong>+ kostenlose Coco-Ausmalbilder jeden Monat</strong>. Kein Spam.',
      name: 'Vorname (optional)',
      email: 'Deine E-Mail',
      btn: 'Erhalten und herunterladen',
      loading: 'Senden…',
      err: 'Ungültige E-Mail.',
      errNet: 'Netzwerkfehler.',
      close: 'Schließen'
    },
    ar: {
      title: 'قبل التنزيل...',
      sub: 'اترك بريدك الإلكتروني لتحصل على الملف <strong>+ صفحات تلوين كوكو مجانية كل شهر</strong>. بلا رسائل مزعجة.',
      name: 'الاسم الأول (اختياري)',
      email: 'بريدك الإلكتروني',
      btn: 'استلام وتنزيل',
      loading: 'جارٍ الإرسال...',
      err: 'البريد الإلكتروني غير صالح. حاول مرة أخرى.',
      errNet: 'مشكلة في الشبكة. حاول مرة أخرى.',
      close: 'إغلاق'
    },
    pt: {
      title: 'Antes de baixar...',
      sub: 'Deixe seu email para receber o arquivo <strong>+ desenhos da Coco para colorir grátis todos os meses</strong>. Sem spam.',
      name: 'Nome (opcional)',
      email: 'Seu email',
      btn: 'Receber e baixar',
      loading: 'Enviando...',
      err: 'Email inválido. Tente de novo.',
      errNet: 'Problema de rede. Tente de novo.',
      close: 'Fechar'
    }
  };

  function tr() { return T[getLang()] || T.en; }

  function injectCss() {
    if (document.getElementById('us-emailgate-css')) return;
    var s = document.createElement('style');
    s.id = 'us-emailgate-css';
    s.textContent =
      '.us-eg-ov{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:99998;display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;visibility:hidden;transition:opacity .25s,visibility .25s;backdrop-filter:blur(4px)}' +
      '.us-eg-ov.on{opacity:1;visibility:visible}' +
      '.us-eg-box{background:#fff;max-width:420px;width:100%;border-radius:18px;padding:30px 26px 22px;box-shadow:0 22px 60px rgba(0,0,0,.28);text-align:center;transform:translateY(15px) scale(.97);transition:transform .25s;border-top:6px solid #ff69b4;font-family:Inter,system-ui,-apple-system,Arial,sans-serif}' +
      '.us-eg-ov.on .us-eg-box{transform:none}' +
      '.us-eg-close{position:absolute;top:10px;right:12px;width:32px;height:32px;border-radius:50%;border:none;background:rgba(0,0,0,.06);font-size:18px;cursor:pointer;color:#555}' +
      '.us-eg-h{margin:0 0 8px;font-size:21px;color:#0d1421}' +
      '.us-eg-p{margin:0 0 18px;color:#555;font-size:14.5px;line-height:1.5}' +
      '.us-eg-in{display:block;width:100%;box-sizing:border-box;padding:12px 14px;margin-bottom:10px;border:2px solid #e5e7eb;border-radius:10px;font-size:15px;font-family:inherit;outline:none}' +
      '.us-eg-in:focus{border-color:#ff69b4}' +
      '.us-eg-btn{display:block;width:100%;padding:13px;background:#ff69b4;color:#fff;border:none;border-radius:30px;font-weight:700;font-size:15px;cursor:pointer;margin-top:6px;transition:background .15s}' +
      '.us-eg-btn:hover{background:#ff4fa7}' +
      '.us-eg-btn:disabled{opacity:.6;cursor:wait}' +
      '.us-eg-err{color:#dc2626;font-size:13px;margin:6px 0 0;min-height:18px}';
    document.head.appendChild(s);
  }

  window.__usEmailGateOpen = function(onSuccess) {
    if (!shouldGate()) { onSuccess && onSuccess(); return; }
    openModal(onSuccess);
  };

  function openModal(onSuccess) {
    injectCss();
    var t = tr();
    var ov = document.createElement('div');
    ov.className = 'us-eg-ov';
    ov.setAttribute('role', 'dialog');
    ov.setAttribute('aria-modal', 'true');
    ov.innerHTML =
      '<div class="us-eg-box" style="position:relative">' +
      '<button class="us-eg-close" aria-label="' + t.close + '">&times;</button>' +
      '<h3 class="us-eg-h">' + t.title + '</h3>' +
      '<p class="us-eg-p">' + t.sub + '</p>' +
      '<input class="us-eg-in" type="text" id="usEgName" placeholder="' + t.name + '" autocomplete="given-name">' +
      '<input class="us-eg-in" type="email" id="usEgEmail" placeholder="' + t.email + '" required autocomplete="email">' +
      '<button class="us-eg-btn" id="usEgSubmit">' + t.btn + '</button>' +
      '<div class="us-eg-err" id="usEgErr"></div>' +
      '</div>';
    document.body.appendChild(ov);
    requestAnimationFrame(function () { ov.classList.add('on'); });

    var inputEmail = ov.querySelector('#usEgEmail');
    var inputName  = ov.querySelector('#usEgName');
    var btn        = ov.querySelector('#usEgSubmit');
    var errBox     = ov.querySelector('#usEgErr');
    var closeBtn   = ov.querySelector('.us-eg-close');
    setTimeout(function () { try { inputEmail.focus(); } catch (e) {} }, 250);

    function close() {
      ov.classList.remove('on');
      setTimeout(function () { try { ov.remove(); } catch (e) {} }, 250);
    }
    closeBtn.addEventListener('click', close);
    ov.addEventListener('click', function (e) { if (e.target === ov) close(); });
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', escHandler); }
    });

    function submit() {
      var email = (inputEmail.value || '').trim();
      var name  = (inputName.value || '').trim();
      var ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      if (!ok) { errBox.textContent = tr().err; inputEmail.focus(); return; }
      btn.disabled = true;
      btn.textContent = tr().loading;
      errBox.textContent = '';
      fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, name: name, lang: getLang() })
      }).then(function (r) {
        if (!r.ok && r.status !== 204) throw new Error('bad');
        markEmailGiven();
        close();
        try { onSuccess(); } catch (e) {}
      }).catch(function () {
        btn.disabled = false;
        btn.textContent = tr().btn;
        errBox.textContent = tr().errNet;
      });
    }
    btn.addEventListener('click', submit);
    inputEmail.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });
    inputName.addEventListener('keydown',  function (e) { if (e.key === 'Enter') submit(); });
  }

  window.usEmailGate = function (cb) {
    if (typeof cb !== 'function') cb = function () {};
    if (!shouldGate()) { cb(); return; }
    openModal(cb);
  };

  document.addEventListener('click', function (e) {
    if (!shouldGate()) return;
    var el = e.target && e.target.closest ? e.target.closest('[data-email-gate]') : null;
    if (!el) return;
    if (el.dataset && el.dataset.usEgDone === '1') return;

    var action = el.getAttribute('data-email-gate') || '';
    if (!/(download|export|save)/i.test(action)) return;

    e.preventDefault();
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();

    openModal(function () {
      try { if (el.dataset) el.dataset.usEgDone = '1'; } catch (er) {}
      el.click();
      setTimeout(function () { try { if (el.dataset) delete el.dataset.usEgDone; } catch (er) {} }, 1000);
    });
  }, true);
})();
