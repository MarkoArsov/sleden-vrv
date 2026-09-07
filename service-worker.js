const CACHE_NAME = 'sleden-vrv-v6';
const APP_SHELL = [
  './',
  './index.html',
  './support.js',
  './favicon.svg',
  './apple-touch-icon.png',
  './icon-512.png',
  './manifest.webmanifest',
  './pwa.js?v=6',
  './hikes.json',
  './_ds/classical-668ace92-beca-41c2-b77b-3915a45aeb50/styles.css',
  './_ds/classical-668ace92-beca-41c2-b77b-3915a45aeb50/_ds_bundle.js'
];
const HIKES_PATH = new URL('./hikes.json', self.location.href).pathname;

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
  )).then(() => self.clients.claim()));
});

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    throw error;
  }
}

async function notifyHikesUpdated() {
  const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  clients.forEach((client) => client.postMessage({ type: 'hikes-updated' }));
}

async function staleWhileRevalidate(request, event) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  const refresh = fetch(request).then(async (response) => {
    if (!response || !response.ok) return response;
    const previous = await cache.match(request);
    const changed = !previous || await previous.clone().text() !== await response.clone().text();
    await cache.put(request, response.clone());
    if (changed && previous) await notifyHikesUpdated();
    return response;
  });
  event.waitUntil(refresh.catch(() => {}));
  return cached || refresh;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname === HIKES_PATH) {
    event.respondWith(staleWhileRevalidate(request, event));
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request).catch(() => caches.match('./index.html')));
    return;
  }

  event.respondWith(caches.match(request).then((cached) => cached || networkFirst(request)));
});
