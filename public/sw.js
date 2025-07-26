const CACHE_NAME = "smartquotr-v1";  // 🔁 Increment this to bust old caches

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('smartquotr-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/static/style.css',
        '/static/script.js',
        '/public/logo.png'
      ]);
    })
  );
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((resp) => {
      return resp || fetch(e.request);
    })
  );
});

// ✅ Clean up old caches
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.map((name) => {
          if (name !== CACHE_NAME) {
            console.log("🧹 Deleting old cache:", name);
            return caches.delete(name);
          }
        })
      );
    })
  );
});
