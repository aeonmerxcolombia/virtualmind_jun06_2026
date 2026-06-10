// Helper para fetch con token automático
function getToken() {
    return localStorage.getItem("token");
}

async function fetchConToken(url, options = {}) {
    const token = getToken();
    const headers = {
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Si la URL no tiene protocolo, añadir la base
    if (!url.startsWith('http')) {
        url = 'https://gestordecursos.pegui.edu.co:8000' + url;
    }

    return fetch(url, { ...options, headers });
}

// Envolvemos el interceptor para que no choque si el script se carga 2 veces
(function() {
    // Si ya interceptamos el fetch previamente, salimos silenciosamente
    if (window.__fetchIntercepted) return;

    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {}) {
        const token = getToken();

        // Validamos que url sea un string antes de usar includes o startsWith
        if (token && typeof url === 'string' && (url.includes('gestordecursos.pegui.edu.co') || url.startsWith('/'))) {
            options = options || {};
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }

        return originalFetch(url, options);
    };

    // Marcamos que ya hicimos el trabajo
    window.__fetchIntercepted = true;
})();
