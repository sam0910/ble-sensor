const CACHE_NAME = "narmi-cache-v1";
const urlsToCache = [
    "/",
    "/index.html",
    "/manifest.json",
    "/icons/icon-192x192.png",
    "/icons/icon-512x512.png",
    "/assets/index-CLS2btZ0.js",
    "/assets/index-B5-xJlYm.css",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            // Cache hit - return response
            if (response) {
                return response;
            }

            return fetch(event.request).then((response) => {
                // Check if we received a valid response
                if (!response || response.status !== 200 || response.type !== "basic") {
                    return response;
                }

                // Clone the response
                const responseToCache = response.clone();

                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });

                return response;
            });
        })
    );
});

self.addEventListener("activate", (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener("sync", (event) => {
    if (event.tag === "sync-data") {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    // Implement your background sync logic here
}

self.addEventListener("periodicsync", async (event) => {
    if (event.tag === "ble-sync") {
        event.waitUntil(syncBLEData());
    }
});

async function syncBLEData() {
    try {
        // Store BLE data in IndexedDB or cache for offline access
        const bleData = await getBLEData();
        if (bleData) {
            await caches.open("ble-data").then((cache) => {
                return cache.put("/ble-data", new Response(JSON.stringify(bleData)));
            });
        }
    } catch (error) {
        console.error("Background sync failed:", error);
    }
}
