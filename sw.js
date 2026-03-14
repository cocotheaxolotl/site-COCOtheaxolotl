// Coco the Axolotl — Service Worker v2
const CACHE_STATIC = 'coco-static-v2';
const CACHE_IMAGES = 'coco-images-v1';

// Pages et assets mis en cache au démarrage
const PRECACHE = [
  '/',
  '/kids-games/',
  '/puzzle/',
  '/bubble-pop/',
  '/memory/',
  '/common.css',
  '/coco.png',
  '/favicon.ico',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/puzzle/win.mp3',
  '/puzzle/images/index.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_STATIC)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  // Supprimer les vieux caches
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys
        .filter(k => k !== CACHE_STATIC && k !== CACHE_IMAGES)
        .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Images puzzle : cache-first (elles ne changent pas souvent)
  if (url.pathname.startsWith('/puzzle/images/') && !url.pathname.endsWith('index.json')) {
    e.respondWith(
      caches.open(CACHE_IMAGES).then(cache =>
        cache.match(e.request).then(cached => {
          if (cached) return cached;
          return fetch(e.request).then(response => {
            cache.put(e.request, response.clone());
            return response;
          });
        })
      )
    );
    return;
  }

  // Tout le reste : network-first, fallback cache
  e.respondWith(
    fetch(e.request)
      .then(response => {
        if (e.request.method === 'GET' && response.status === 200) {
          caches.open(CACHE_STATIC).then(cache => cache.put(e.request, response.clone()));
        }
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});
