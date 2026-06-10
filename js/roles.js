// js/roles.js - Sistema de Roles y Permisos para VirtualMind
// Todas las funciones son globales (sin export)

const API_BASE = 'https://gestordecursos.pegui.edu.co:8000';

// ==================== INTERCEPTOR GLOBAL PARA 401 ====================
(function() {
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            if (response.status === 401) {
                console.log('Token pudo haber expirado o error de autenticación');
                // Ya no cierra sesión automáticamente
                // El usuario puede seguir navegando
            }
            return response;
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    };
})();

// ==================== FUNCIONES BÁSICAS ====================
function getToken() {
    return localStorage.getItem('token');
}

function getUserPayload() {
    const token = getToken();
    if (!token) return null;
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch {
        return null;
    }
}

function getUserRoles() {
    const payload = getUserPayload();
    if (!payload) return [];
    return payload.roles || [payload.role].filter(Boolean);
}

function getUserPermissions() {
    const payload = getUserPayload();
    if (!payload) return [];
    return payload.permissions || [];
}

function hasRole(role) {
    return getUserRoles().includes(role);
}

function hasAnyRole(roles) {
    return roles.some(role => hasRole(role));
}

function hasPermission(permission) {
    return getUserPermissions().includes(permission);
}

function hasAnyPermission(permissions) {
    return permissions.some(p => getUserPermissions().includes(p));
}

function hasAllPermissions(permissions) {
    return permissions.every(p => getUserPermissions().includes(p));
}

function requireAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

function requireRole(allowedRoles, redirectUrl) {
    redirectUrl = redirectUrl || '/';
    if (!requireAuth()) return false;
    if (!hasAnyRole(allowedRoles)) {
        alert('No tienes permiso para acceder a esta sección.');
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

function requirePermission(permission, redirectUrl) {
    redirectUrl = redirectUrl || '/';
    if (!requireAuth()) return false;
    if (!hasPermission(permission)) {
        alert('No tienes permiso para esta acción.');
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

function hideIfNoRole(selector, roles) {
    const element = document.querySelector(selector);
    if (element && !hasAnyRole(roles)) {
        element.style.display = 'none';
    }
}

function showIfHasRole(selector, roles) {
    const element = document.querySelector(selector);
    if (element && hasAnyRole(roles)) {
        element.style.display = '';
    }
}

function hideIfNoPermission(selector, permission) {
    const element = document.querySelector(selector);
    if (element && !hasPermission(permission)) {
        element.style.display = 'none';
    }
}

function hideIfNoPermissions(selector, permissions) {
    const element = document.querySelector(selector);
    if (element && !hasAnyPermission(permissions)) {
        element.style.display = 'none';
    }
}

function showIfHasPermission(selector, permission) {
    const element = document.querySelector(selector);
    if (element && hasPermission(permission)) {
        element.style.display = '';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('termsAccepted');
    window.location.href = '/login.html';
}

function getUserName() {
    const payload = getUserPayload();
    return payload?.name || payload?.nombre || payload?.email || 'Usuario';
}

function initRoleGuard(requiredRoles, redirectUrl) {
    redirectUrl = redirectUrl || '/';
    if (!requireAuth()) return false;
    if (requiredRoles && requiredRoles.length > 0 && !hasAnyRole(requiredRoles)) {
        alert('No tienes permiso para acceder a esta página.');
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

function initPermissionGuard(requiredPermissions, redirectUrl) {
    redirectUrl = redirectUrl || '/';
    if (!requireAuth()) return false;
    if (requiredPermissions && requiredPermissions.length > 0 && !hasAnyPermission(requiredPermissions)) {
        alert('No tienes los permisos necesarios para esta página.');
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

async function apiCall(endpoint, options) {
    options = options || {};
    const token = getToken();
    if (!token) throw new Error('No autenticado');
    
    const defaultOptions = {
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    };
    
    const response = await fetch(API_BASE + endpoint, Object.assign({}, defaultOptions, options, {
        headers: Object.assign({}, defaultOptions.headers, options.headers)
    }));
    
    if (response.status === 401) {
        console.warn('Token expirado o inválido');
        // Ya no cierra sesión automáticamente
        throw new Error('Token expirado o inválido');
    }
    if (response.status === 403) {
        throw new Error('No tienes permiso para esta acción');
    }
    return response;
}

// ==================== CONFIGURACIÓN DE MENÚS ====================
const MENU_PERMISSIONS = {
    'menu-proyectos': ['proyectos_crear', 'proyectos_consultar'],
    'menu-crear-proyecto': ['proyectos_crear'],
    'menu-listar-proyectos': ['proyectos_consultar'],
    'menu-usuarios': ['usuarios_crear'],
    'menu-crear-usuario': ['usuarios_crear'],
    'menu-roles': ['roles_permisos_gestionar'],
    'menu-gestionar-roles': ['roles_permisos_gestionar'],
    'menu-ia-imagen': ['ia_produccion_imagen'],
    'menu-ia-audio': ['ia_produccion_audio'],
    'menu-ia-video': ['ia_videocast_crear'],
    'menu-ia-podcast': ['ia_podcast_crear']
};

function initMenuPermissions() {
    if (!MENU_PERMISSIONS) return;
    Object.entries(MENU_PERMISSIONS).forEach(function(entry) {
        const menuId = entry[0];
        const requiredPermissions = entry[1];
        const element = document.getElementById(menuId);
        if (element && !hasAnyPermission(requiredPermissions)) {
            element.style.display = 'none';
        }
    });
}

function initAllGuards(requiredRoles, requiredPermissions, redirectUrl) {
    redirectUrl = redirectUrl || '/';
    if (!requireAuth()) return false;
    if (requiredRoles && requiredRoles.length > 0 && !hasAnyRole(requiredRoles)) {
        alert('No tienes permiso para acceder a esta página.');
        window.location.href = redirectUrl;
        return false;
    }
    if (requiredPermissions && requiredPermissions.length > 0 && !hasAnyPermission(requiredPermissions)) {
        alert('No tienes los permisos necesarios.');
        window.location.href = redirectUrl;
        return false;
    }
    initMenuPermissions();
    return true;
}

// Exponer en window
window.Roles = {
    getToken: getToken,
    getUserPayload: getUserPayload,
    getUserRoles: getUserRoles,
    getUserPermissions: getUserPermissions,
    hasRole: hasRole,
    hasAnyRole: hasAnyRole,
    hasPermission: hasPermission,
    hasAnyPermission: hasAnyPermission,
    hasAllPermissions: hasAllPermissions,
    requireAuth: requireAuth,
    requireRole: requireRole,
    requirePermission: requirePermission,
    hideIfNoRole: hideIfNoRole,
    showIfHasRole: showIfHasRole,
    hideIfNoPermission: hideIfNoPermission,
    hideIfNoPermissions: hideIfNoPermissions,
    showIfHasPermission: showIfHasPermission,
    logout: logout,
    getUserName: getUserName,
    initRoleGuard: initRoleGuard,
    initPermissionGuard: initPermissionGuard,
    initMenuPermissions: initMenuPermissions,
    initAllGuards: initAllGuards,
    apiCall: apiCall,
    MENU_PERMISSIONS: MENU_PERMISSIONS
};

// Funciones ya están disponibles globalmente por ser funciones declaradas con function
