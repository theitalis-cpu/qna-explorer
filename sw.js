const CACHE = 'qna-v1';
const ASSETS = [
  '/qna-explorer/',
  '/qna-explorer/index.html',
  '/qna-explorer/manifest.json',
  '/qna-explorer/icon-192.png',
  '/qna-explorer/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // For API calls — always go network
  if (e.request.url.includes('search.sbms.io')) return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
