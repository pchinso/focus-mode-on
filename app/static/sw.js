/* Focus Mode On — minimal service worker.
 * Caches static assets (cache-first) so the app shell loads instantly and
 * offline. Dynamic, auth'd pages are always served from the network. */
const CACHE = "fmo-static-v1";
const ASSETS = [
  "/static/css/tokens.css",
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/favicon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
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
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (!url.pathname.startsWith("/static/")) return; // network handles dynamic pages
  event.respondWith(
    caches.match(event.request).then(
      (cached) =>
        cached ||
        fetch(event.request).then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(event.request, copy));
          return resp;
        })
    )
  );
});
