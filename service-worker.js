const CACHE_NAME = 'virtualmind-cache-v2'; // Incrementa la versión para forzar actualización
const urlsToCache = [
  // URLs relativas funcionan mejor si el SW está en la raíz
  '/', // Cachea la raíz (usualmente index.html)
  '/index.html', // Cachea explícitamente index.html
  '/manifest.json',
  '/assets/logo.png',
  // Añade aquí otros archivos CRÍTICOS para que la app funcione offline
  // Por ejemplo: tu CSS principal, JS principal, íconos importantes
  '/output.css', // Asumiendo que está en la raíz
  // '/js/main.js', // Ejemplo si tienes un JS principal
  // '/assets/login-bg.jpg' // Ejemplo si quieres cachear el fondo
];

// Instalación: Cachea los archivos principales
self.addEventListener('install', (event) => {
  console.log('SW: Instalando v2...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('SW: Cache abierto, añadiendo app shell...');
      // Usamos addAll que es más eficiente y atómico
      return cache.addAll(urlsToCache).catch(error => {
        console.error('SW: Falló al añadir archivos al caché durante la instalación:', error);
        // Podríamos decidir no instalar si el app shell falla
        // throw error;
      });
    }).then(() => {
      // Forzar la activación inmediata del nuevo SW
      return self.skipWaiting();
    })
  );
});

// Activación: Limpia cachés antiguas y toma control
self.addEventListener('activate', (event) => {
  console.log('SW: Activando v2...');
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log(`SW: Borrando caché obsoleta: ${cacheName}`);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Tomar control inmediato de las páginas abiertas
      return self.clients.claim();
    })
  );
});

// Fetch: Intercepta solicitudes y aplica estrategias
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // --- ESTRATEGIAS ---

  // 1. Ignorar solicitudes no-GET (POST, PUT, etc.) y de extensiones
  if (event.request.method !== 'GET' || requestUrl.protocol === 'chrome-extension:') {
    // console.log('SW: Ignorando solicitud no-GET o de extensión:', event.request.url);
    return; // Dejar que el navegador maneje estas solicitudes normalmente
  }

  // 2. Estrategia para URLs de TERCEROS (Google APIs, Facebook SDK, etc.)
  //   - Ir a la red directamente. No intentar cachear.
  //   - Capturar errores de red básicos (como los bloqueados).
  if (requestUrl.origin !== self.location.origin) {
    // console.log('SW: Manejando solicitud externa (solo red):', event.request.url);
    event.respondWith(
      fetch(event.request).catch(error => {
        // Este catch manejará el error "Failed to fetch" para solicitudes bloqueadas (ERR_BLOCKED_BY_CLIENT)
        // o fallos de red genuinos para recursos externos.
        console.warn('SW: Fetch fallido para URL externa (puede ser normal si fue bloqueada):', event.request.url, error.message);
        // Devolvemos una respuesta de error genérica o simplemente dejamos que falle (lo que mostrará el error en la consola)
        // No devolvemos nada aquí para que el navegador muestre el error original (ej. ERR_BLOCKED_BY_CLIENT)
        // Si quisiéramos ocultar el error, podríamos devolver: return new Response('', { status: 503, statusText: 'Service Unavailable' });
      })
    );
    return; // Importante: termina aquí para URLs externas
  }

  // 3. Estrategia para recursos PROPIOS (misma origen)
  //   - Cache First, then Network (para el app shell y assets cacheados en 'install')
  //   - Con fallback a red y manejo de error si la red falla.
  // console.log('SW: Manejando solicitud propia (Cache First):', event.request.url);
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // Si está en caché, devolverlo
      if (cachedResponse) {
        // console.log('SW: Sirviendo desde caché:', event.request.url);
        return cachedResponse;
      }

      // Si no está en caché, ir a la red
      // console.log('SW: No en caché, yendo a red:', event.request.url);
      return fetch(event.request).then((networkResponse) => {
          // Opcional: Podrías querer cachear la respuesta aquí dinámicamente
          // if (networkResponse && networkResponse.ok) {
          //   const responseToCache = networkResponse.clone();
          //   caches.open(CACHE_NAME).then((cache) => {
          //     cache.put(event.request, responseToCache);
          //   });
          // }
          return networkResponse;
        }).catch((error) => {
          // Error al buscar en la red (ej. offline)
          console.error('SW: Fetch de red falló para recurso propio:', event.request.url, error);
          // Opcional: Devolver una página offline personalizada si la tienes cacheada
          // return caches.match('/offline.html');
          // O simplemente dejar que falle y el navegador muestre el error de conexión
        });
    })
  );
});
