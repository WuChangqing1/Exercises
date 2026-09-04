// Training Tracker service worker — scope is limited to /training/ by registration.
const CACHE = "training-tracker-v1";
const ASSET_PREFIXES = ["/static/", "/training/static/"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(["/training/"]))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // Never touch anything outside /training/ or the shared asset paths.
  const isStatic = ASSET_PREFIXES.some((p) => url.pathname.startsWith(p));
  const isTraining = url.pathname.startsWith("/training/");

  if (!isStatic && !isTraining) {
    return;
  }

  // Static assets: cache-first. Dynamic pages: network-first (fallback to cache).
  if (isStatic) {
    event.respondWith(
      caches.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request).then((resp) => {
            const copy = resp.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, copy));
            return resp;
          })
      )
    );
  } else {
    event.respondWith(
      fetch(event.request).catch(() => caches.match("/training/"))
    );
  }
});
