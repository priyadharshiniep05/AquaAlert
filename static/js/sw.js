const CACHE_NAME = 'aquaalert-v1';
const OFFLINE_ASSETS = [
  '/', '/dashboard', '/preparedness',
  '/static/css/style.css', '/static/js/main.js',
  '/static/js/charts.js', '/static/js/map.js'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_ASSETS)));
});

self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : {title: 'AquaAlert', body: 'Flood risk update'};
  e.waitUntil(self.registration.showNotification(data.title, {
    body: data.body, icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png', vibrate: [200, 100, 200],
    data: {url: '/dashboard'}
  }));
});
