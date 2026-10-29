// Share button: a pill in a corner of the page that opens a small menu —
// WhatsApp, email, copy link, download. Self-contained: no dependencies.
//
//   <script src="share.js" defer></script>
//   <script src="share.js" defer data-corner="bottom-left"></script>
//
// The link it shares comes from share-link.json beside the page ({url}),
// which scripts/publish.py writes when it publishes the page. Before that the page
// has no public address, so the menu says so and offers only the download.
//
// data-corner: top-left (default) | top-right | bottom-left | bottom-right.
//   Not top-right inside Flowpad: Flowpad floats its own Share pill there.
// The language follows <html lang>: he, ar, otherwise English.
(() => {
  const script = document.currentScript;
  const TEXT = {
    he: {
      share: 'שיתוף', whatsapp: 'שליחה בווטסאפ', email: 'שליחה במייל', copy: 'העתקת הקישור',
      download: 'הורדה למחשב', copied: 'הקישור הועתק!', message: 'תראו מה בניתי:',
      notYet: 'הדף עוד לא פורסם. בקשו מהסוכן לפרסם אותו כדי לקבל קישור.',
      failCopy: 'לא הצלחנו להעתיק — העתיקו מכאן:', failDownload: 'ההורדה לא הצליחה',
    },
    ar: {
      share: 'مشاركة', whatsapp: 'إرسال عبر واتساب', email: 'إرسال بالبريد', copy: 'نسخ الرابط',
      download: 'تنزيل إلى الحاسوب', copied: 'تم نسخ الرابط!', message: 'انظروا ماذا بنيت:',
      notYet: 'لم تُنشر الصفحة بعد. اطلبوا من المساعد نشرها للحصول على رابط.',
      failCopy: 'لم ننجح في النسخ — انسخوا من هنا:', failDownload: 'فشل التنزيل',
    },
    en: {
      share: 'Share', whatsapp: 'Send on WhatsApp', email: 'Send by email', copy: 'Copy link',
      download: 'Download', copied: 'Link copied!', message: 'Look what I built:',
      notYet: 'This page is not published yet. Ask the assistant to publish it to get a link.',
      failCopy: "Couldn't copy — copy it from here:", failDownload: 'The download failed',
    },
  };
  const lang = (document.documentElement.lang || 'en').slice(0, 2).toLowerCase();
  const text = TEXT[lang] || TEXT.en;
  const corner = script?.dataset.corner || 'top-left';
  const [vertical, horizontal] = corner.split('-');

  // ── the link ─────────────────────────────────────────────────────────────
  // A downloaded copy carries it inline (window.__SHARE_LINK__); a served page reads the file.
  let shareLink = window.__SHARE_LINK__ || null;
  const linkReady = shareLink
    ? Promise.resolve(shareLink)
    : fetch(new URL('share-link.json', location.href), { cache: 'no-store' })
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null)
        .then((j) => (shareLink = j && j.url ? j : null));

  function messageWithLink() {
    return `${text.message} ${document.title}\n${shareLink.url}`;
  }

  // ── actions ──────────────────────────────────────────────────────────────
  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      const area = document.createElement('textarea');
      area.value = value;
      area.setAttribute('readonly', '');
      area.style.cssText = 'position:fixed;opacity:0;inset:0;';
      document.body.append(area);
      area.select();
      const ok = document.execCommand('copy');
      area.remove();
      return ok;
    }
  }

  function blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  const isRelative = (value) => value && !/^(?:[a-z]+:|\/\/|#)/i.test(value);

  // One self-contained .html: styles, scripts and media inlined, so it opens with no folder beside it.
  async function standaloneHtml() {
    if (location.protocol === 'file:') return `<!doctype html>\n${document.documentElement.outerHTML}`;
    const pageUrl = location.href.split('#')[0];
    const source = await (await fetch(pageUrl, { cache: 'no-store' })).text();
    const doc = new DOMParser().parseFromString(source, 'text/html');
    const abs = (value) => new URL(value, pageUrl);

    for (const link of doc.querySelectorAll('link[rel~="stylesheet"][href]')) {
      if (!isRelative(link.getAttribute('href'))) continue;
      const style = doc.createElement('style');
      style.textContent = await (await fetch(abs(link.getAttribute('href')))).text();
      link.replaceWith(style);
    }
    // Inlined scripts move to the end of <body>, in order: an inline script runs where it
    // stands, and a deferred one expected the whole page to exist already.
    const moved = [];
    for (const old of doc.querySelectorAll('script[src]')) {
      if (!isRelative(old.getAttribute('src'))) continue;
      const inline = doc.createElement('script');
      for (const { name, value } of old.attributes) {
        if (name !== 'src' && name !== 'defer' && name !== 'async') inline.setAttribute(name, value);
      }
      inline.textContent = (await (await fetch(abs(old.getAttribute('src')))).text()).replace(/<\/script/gi, '<\\/script');
      old.remove();
      moved.push(inline);
    }
    if (shareLink) {
      const known = doc.createElement('script');
      known.textContent = `window.__SHARE_LINK__ = ${JSON.stringify(shareLink)};`;
      moved.unshift(known);
    }
    doc.body.append(...moved);
    for (const el of doc.querySelectorAll('img[src], audio[src], video[src], source[src], link[rel~="icon"][href]')) {
      const attr = el.hasAttribute('src') ? 'src' : 'href';
      const value = el.getAttribute(attr);
      if (!isRelative(value)) continue;
      el.setAttribute(attr, await blobToDataUrl(await (await fetch(abs(value))).blob()));
    }
    return `<!doctype html>\n${doc.documentElement.outerHTML}`;
  }

  async function download() {
    try {
      const html = await standaloneHtml();
      const name = (document.title || 'page').trim().replace(/[\\/:*?"<>|]+/g, '').slice(0, 60) || 'page';
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
      a.download = `${name}.html`;
      document.body.append(a);
      a.click();
      setTimeout(() => {
        URL.revokeObjectURL(a.href);
        a.remove();
      }, 1000);
    } catch {
      say(text.failDownload);
    }
  }

  // ── UI ───────────────────────────────────────────────────────────────────
  const ICONS = {
    share: '<path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/>',
    whatsapp: '<path d="M3 21l1.6-4.8A8.5 8.5 0 1 1 8 19.6Z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1.2-1.2-1.8-1-1 .8a4 4 0 0 1-2.5-2.5l.8-1-1-1.8Z"/>',
    email: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    copy: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
  };
  const icon = (name) =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

  const style = document.createElement('style');
  style.textContent = `
    .share-pill, .share-menu, .share-toast { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
    .share-pill {
      position: fixed; z-index: 2147483000; ${vertical}: max(12px, env(safe-area-inset-${vertical}));
      ${horizontal}: max(12px, env(safe-area-inset-${horizontal}));
      display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px;
      border: 0; border-radius: 999px; cursor: pointer; font-weight: 600; font-size: 14px; line-height: 1;
      color: #fff; background: rgb(20 20 30 / .72); backdrop-filter: blur(8px);
      box-shadow: 0 4px 14px rgb(0 0 0 / .25); touch-action: manipulation;
      transition: transform .15s ease, background .15s ease;
    }
    .share-pill:hover { background: rgb(20 20 30 / .88); }
    .share-pill:active { transform: scale(.95); }
    .share-pill svg, .share-menu svg { width: 18px; height: 18px; flex: none; }
    .share-menu {
      position: fixed; z-index: 2147483001; ${vertical}: calc(max(12px, env(safe-area-inset-${vertical})) + 46px);
      ${horizontal}: max(12px, env(safe-area-inset-${horizontal}));
      min-width: 230px; max-width: calc(100vw - 24px); padding: 8px; border-radius: 16px;
      color: #fff; background: rgb(20 20 30 / .94); box-shadow: 0 12px 32px rgb(0 0 0 / .35);
    }
    .share-menu[hidden] { display: none; }
    .share-menu button {
      display: flex; align-items: center; gap: 10px; width: 100%; padding: 12px; border: 0; border-radius: 10px;
      color: inherit; background: none; font: 600 15px/1.2 inherit; text-align: start; cursor: pointer;
    }
    .share-menu button:hover:not(:disabled) { background: rgb(255 255 255 / .1); }
    .share-menu button:disabled { opacity: .4; cursor: default; }
    .share-menu p { margin: 6px 12px 4px; font-size: 13px; line-height: 1.4; opacity: .75; }
    .share-pill:focus-visible, .share-menu button:focus-visible { outline: 3px solid #ffd54a; outline-offset: 2px; }
    .share-toast {
      position: fixed; z-index: 2147483002; left: 50%; bottom: max(24px, env(safe-area-inset-bottom));
      transform: translate(-50%, 20px); opacity: 0; pointer-events: none;
      max-width: min(90vw, 420px); padding: 12px 18px; border-radius: 14px; text-align: center;
      font-weight: 600; font-size: 15px; line-height: 1.4; overflow-wrap: anywhere;
      color: #fff; background: rgb(20 20 30 / .92); box-shadow: 0 8px 24px rgb(0 0 0 / .3);
      transition: opacity .2s ease, transform .2s ease;
    }
    .share-toast.show { opacity: 1; transform: translate(-50%, 0); pointer-events: auto; user-select: all; }
    @media (prefers-reduced-motion: reduce) { .share-pill, .share-toast { transition: none; } }
  `;

  const pill = document.createElement('button');
  pill.type = 'button';
  pill.className = 'share-pill';
  pill.setAttribute('aria-haspopup', 'menu');
  pill.setAttribute('aria-expanded', 'false');
  pill.innerHTML = icon('share');
  pill.append(text.share);

  const menu = document.createElement('div');
  menu.className = 'share-menu';
  menu.setAttribute('role', 'menu');
  menu.hidden = true;

  const toast = document.createElement('div');
  toast.className = 'share-toast';
  toast.setAttribute('role', 'status');
  let hideTimer;
  function say(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => toast.classList.remove('show'), 4000);
  }

  function item(name, label, needsLink, run) {
    const b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('role', 'menuitem');
    b.innerHTML = icon(name);
    b.append(label);
    b.dataset.needsLink = needsLink ? '1' : '';
    b.addEventListener('click', () => {
      close();
      run();
    });
    return b;
  }
  const note = document.createElement('p');
  menu.append(
    item('whatsapp', text.whatsapp, true, () =>
      window.open(`https://wa.me/?text=${encodeURIComponent(messageWithLink())}`, '_blank', 'noopener'),
    ),
    item('email', text.email, true, () => {
      location.href = `mailto:?subject=${encodeURIComponent(document.title)}&body=${encodeURIComponent(messageWithLink())}`;
    }),
    item('copy', text.copy, true, async () => {
      if (await copyText(shareLink.url)) say(text.copied);
      else say(`${text.failCopy} ${shareLink.url}`);
    }),
    item('download', text.download, false, download),
    note,
  );

  async function open() {
    await linkReady;
    for (const b of menu.querySelectorAll('button')) b.disabled = b.dataset.needsLink === '1' && !shareLink;
    note.textContent = text.notYet;
    note.hidden = !!shareLink;
    menu.hidden = false;
    pill.setAttribute('aria-expanded', 'true');
    menu.querySelector('button:not(:disabled)')?.focus();
  }
  function close() {
    menu.hidden = true;
    pill.setAttribute('aria-expanded', 'false');
  }

  // A tap on the share UI must never reach the game underneath it.
  for (const el of [pill, menu]) {
    for (const type of ['pointerdown', 'touchstart', 'mousedown', 'keydown']) {
      el.addEventListener(type, (event) => event.stopPropagation(), { passive: true });
    }
  }
  pill.addEventListener('click', (event) => {
    event.stopPropagation();
    pill.blur(); // so the game's Space / Enter keys don't press it again
    if (menu.hidden) open();
    else close();
  });
  document.addEventListener('click', (event) => {
    if (!menu.hidden && !menu.contains(event.target)) close();
  });
  menu.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      close();
      pill.focus();
    }
  });

  function mount() {
    document.head.append(style);
    document.body.append(pill, menu, toast);
  }
  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
