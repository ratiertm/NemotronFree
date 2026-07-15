// 서비스워커: PWA 설치 요건 충족 + 앱 셸 캐시.
// 네비게이션(HTML)은 network-first 로 항상 최신본을 받고, 오프라인일 때만 캐시로 폴백.
// 정적 자산(js/png/manifest)은 cache-first. API 는 항상 네트워크(캐시 안 함).
const CACHE = "nemo-shell-v5";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icon-192.png", "/icon-512.png",
  "/marked.min.js", "/purify.min.js"];

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
  // API 는 서비스워커가 관여하지 않음(항상 네트워크)
  if (url.pathname.startsWith("/api/")) return;

  // 네비게이션 요청(HTML): network-first → 배포하면 즉시 최신본 반영
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("/", copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(e.request).then((r) => r || caches.match("/")))
    );
    return;
  }

  // 정적 자산: cache-first, 없으면 네트워크
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
