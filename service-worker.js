var CACHE_NAME = 'virtualmind-cache-v3';
var BASE = self.location.pathname.indexOf('/staging') === 0 ? '/staging' : '';
var H = '.html';
var urlsToCache = [
  BASE + '/',
  BASE + '/index' + H,
  BASE + '/manifest.json',
  BASE + '/assets/logo.png',
  BASE + '/assets/icon-192x192.png',
  BASE + '/assets/icon-512x512.png',
  BASE + '/output.css',
  BASE + '/css/themes.css',
  BASE + '/css/theme-white.css',
  BASE + '/js/theme-manager.js',
  BASE + '/js/fetch-con-token.js',
  BASE + '/login' + H,
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(urlsToCache);
    }).then(function() { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(event) {
  var whitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.map(function(name) {
          if (whitelist.indexOf(name) === -1) return caches.delete(name);
        })
      );
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(event) {
  var url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.protocol === 'chrome-extension:') return;
  if (url.origin !== self.location.origin) {
    event.respondWith(fetch(event.request).catch(function() { return new Response('', {status:503}); }));
    return;
  }
  event.respondWith(
    caches.match(event.request).then(function(cached) {
      if (cached) return cached;
      return fetch(event.request).then(function(response) {
        if (response && response.ok && response.type === 'basic') {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) { cache.put(event.request, clone); });
        }
        return response;
      }).catch(function() { return caches.match(BASE + '/index' + H); });
    })
  );
});
