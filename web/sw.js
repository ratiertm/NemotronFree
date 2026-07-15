// 최소 서비스워커: 설치 가능(PWA) 요건 충족 + 앱 셸 캐시.
// API 응답은 캐시하지 않는다(항상 네트워크).
const CACHE = "nemo-shell-v2";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icon-192.png", "/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // API 는 항상 네트워크
  if (url.pathname.startsWith("/api/")) return;
  // 그 외: 캐시 우선, 없으면 네트워크
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
