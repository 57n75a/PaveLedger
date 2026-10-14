// PaveLedger service worker: open the app without signal and keep the last workspace that was loaded.
// Changes made offline are queued in the page (IndexedDB) and sent when the connection returns.
const VERSION = 'pl-v1';
const SHELL = VERSION + '-shell';
const DATA = VERSION + '-data';
const STATIC = /^\/(_next\/static\/|fonts\/|flags\/|icons\/|demo\/|logo|favicon)/;

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL).then(c => c.addAll(['/', '/report', '/manifest.webmanifest']).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('message', event => {
  // Signing out removes the stored workspace from this device.
  if (event.data === 'clear-data') event.waitUntil(caches.delete(DATA));
});

async function networkFirst(request, cacheName, key) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(key || request, response.clone());
    return response;
  } catch (err) {
    const hit = await cache.match(key || request, {ignoreSearch: false});
    if (hit) { const h = new Headers(hit.headers); h.set('X-PaveLedger-Offline', '1'); return new Response(await hit.blob(), {status: 200, headers: h}); }
    throw err;
  }
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // The workspace snapshot: always fresh when online, last copy when offline.
  if (url.pathname === '/api/workspace') { event.respondWith(networkFirst(req, DATA, new Request(url.pathname + url.search))); return; }
  if (url.pathname.startsWith('/api/')) return;

  if (STATIC.test(url.pathname)) {
    event.respondWith(caches.open(SHELL).then(async c => (await c.match(req)) || fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; })));
    return;
  }
  if (req.mode === 'navigate') {
    event.respondWith(networkFirst(req, SHELL).catch(async () => (await caches.match('/')) || Response.error()));
  }
});
