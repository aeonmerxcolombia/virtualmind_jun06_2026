(function() {
  const API_BASE = 'https://gestordecursos.pegui.edu.co:8000';

  function getToken() {
    return localStorage.getItem('token');
  }

  function getRol() {
    const match = window.location.pathname.match(/\/r\/([^/]+)\//);
    return match ? match[1] : 'superadmin';
  }

  function apiUrl(path) {
    return API_BASE + path;
  }

  const ROLES_CON_VISTA_RESTRINGIDA = ['autor'];

  async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = { ...options.headers };
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    const rol = getRol();
    if (ROLES_CON_VISTA_RESTRINGIDA.includes(rol)) {
      headers['X-Rol-Vista'] = rol;
    }
    const resp = await fetch(apiUrl(path), { ...options, headers });
    if (!resp.ok) throw new Error('Error del servidor: ' + resp.status);
    return resp.json();
  }

  const cacheClientes = {};
  async function getNombreCliente(client_id) {
    if (!client_id) return '';
    if (cacheClientes[client_id]) return cacheClientes[client_id];
    try {
      const data = await apiFetch('/users/' + client_id);
      const nombre = data.name || data.nombre || client_id;
      cacheClientes[client_id] = nombre;
      return nombre;
    } catch {
      return client_id;
    }
  }

  function getEstadoBadge(estado) {
    const badges = {
      'Planificado': 'bg-blue-100 text-blue-800',
      'En desarrollo': 'bg-yellow-100 text-yellow-800',
      'Aprobado': 'bg-green-100 text-green-800',
      'Aplazado': 'bg-orange-100 text-orange-800',
      'Finalizado': 'bg-emerald-100 text-emerald-800',
      'Cancelado': 'bg-red-100 text-red-800'
    };
    const cls = badges[estado] || 'bg-gray-100 text-gray-800';
    return '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ' + cls + '">' + (estado || '---') + '</span>';
  }

  window.cargarProyectos = async function(containerId) {
    const container = document.getElementById(containerId || 'tablaProyectos');
    if (!container) return;

    const rol = getRol();

    container.innerHTML = `
      <div class="py-16 text-center">
        <div class="inline-flex items-center gap-3 text-gray-500 text-lg">
          <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
          Cargando proyectos...
        </div>
      </div>`;

    try {
      const proyectos = await apiFetch('/projects/');

      if (!proyectos || !proyectos.length) {
        container.innerHTML = `
          <div class="py-16 text-center">
            <div class="text-6xl mb-4">📋</div>
            <div class="text-gray-500 text-lg">No hay proyectos asignados</div>
            <p class="text-gray-400 mt-2">No tienes proyectos asignados actualmente</p>
          </div>`;
        return;
      }

      const nombresClientes = await Promise.all(
        proyectos.map(p => getNombreCliente(p.client_id))
      );

      const rows = proyectos.map((proj, idx) => {
        const c = nombresClientes[idx] || '---';
        const initial = c.charAt(0).toUpperCase();
        return `
          <tr class="border-b border-gray-100 hover:bg-indigo-50/50 transition-colors">
            <td class="px-4 py-3 whitespace-nowrap">
              <span class="inline-flex items-center justify-center w-8 h-8 bg-indigo-100 text-indigo-800 rounded-full text-xs font-bold">${proj.id}</span>
            </td>
            <td class="px-4 py-3">
              <div class="font-medium text-gray-900">${proj.name || '---'}</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white text-xs font-bold">${initial}</div>
                <span class="text-gray-700 text-sm">${c}</span>
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">${getEstadoBadge(proj.estado)}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">${proj.tipo_proyecto || '---'}</td>
            <td class="px-4 py-3 whitespace-nowrap text-xs text-gray-500">
              ${proj.start_date ? 'Inicio: ' + proj.start_date : ''}
              ${proj.end_date ? '<br>Fin: ' + proj.end_date : ''}
              ${!proj.start_date && !proj.end_date ? '---' : ''}
            </td>
            <td class="px-4 py-3">
              <div class="text-xs text-gray-600 max-w-xs truncate">${proj.description || '---'}</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex gap-1.5">
                <button onclick="verDetalleProyecto(${proj.id})" class="bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors">Ver</button>
                <button onclick="irADocumentos(${proj.id})" class="bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors">Docs</button>
              </div>
            </td>
          </tr>`;
      }).join('');

      container.innerHTML = `
        <div class="overflow-x-auto rounded-xl">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
                <th class="px-4 py-3 text-left font-semibold">ID</th>
                <th class="px-4 py-3 text-left font-semibold">Proyecto</th>
                <th class="px-4 py-3 text-left font-semibold">Cliente</th>
                <th class="px-4 py-3 text-left font-semibold">Estado</th>
                <th class="px-4 py-3 text-left font-semibold">Tipo</th>
                <th class="px-4 py-3 text-left font-semibold">Fechas</th>
                <th class="px-4 py-3 text-left font-semibold">Descripción</th>
                <th class="px-4 py-3 text-left font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-100">${rows}</tbody>
          </table>
        </div>`;
    } catch (e) {
      container.innerHTML = `
        <div class="py-16 text-center">
          <div class="text-6xl mb-4">⚠️</div>
          <div class="text-red-500 text-lg font-semibold mb-2">Error al cargar proyectos</div>
          <p class="text-gray-500 text-sm">${e.message}</p>
          <button onclick="cargarProyectos('${containerId || 'tablaProyectos'}')" class="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-6 py-2 font-semibold transition-colors">Reintentar</button>
        </div>`;
    }
  };

  window.verDetalleProyecto = async function(projectId) {
    const rol = getRol();
    try {
      const proj = await apiFetch('/projects/' + projectId);
      const nombreCliente = await getNombreCliente(proj.client_id);

      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm';
      modal.style.animation = 'fadeIn 0.2s ease-out';
      modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-y-auto" style="animation: slideUp 0.3s ease-out">
          <div class="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4 rounded-t-2xl flex justify-between items-center sticky top-0">
            <h2 class="text-xl font-bold text-white truncate pr-4">${proj.name || 'Proyecto'}</h2>
            <button onclick="this.closest('.fixed').remove()" class="text-white/80 hover:text-white text-2xl leading-none">&times;</button>
          </div>
          <div class="p-6 space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Estado</label>
                <div class="mt-1">${getEstadoBadge(proj.estado)}</div>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Cliente</label>
                <p class="mt-1 text-gray-900 font-medium">${nombreCliente || '---'}</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Código de Referencia</label>
                <p class="mt-1 text-gray-900 font-mono text-sm">${proj.codigo_referencia || '---'}</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Tipo de Proyecto</label>
                <p class="mt-1 text-gray-900">${proj.tipo_proyecto || '---'}${proj.tipo_proyecto_personalizado ? ' (' + proj.tipo_proyecto_personalizado + ')' : ''}</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha de Inicio</label>
                <p class="mt-1 text-gray-900">${proj.start_date || '---'}</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha de Fin</label>
                <p class="mt-1 text-gray-900">${proj.end_date || '---'}</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Horas del Curso</label>
                <p class="mt-1 text-gray-900">${proj.horas_curso || '0'}h</p>
              </div>
              <div class="bg-gray-50 rounded-xl p-4">
                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Idioma</label>
                <p class="mt-1 text-gray-900">${proj.idioma || '---'}</p>
              </div>
            </div>
            ${proj.description ? `
            <div class="bg-gray-50 rounded-xl p-4">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Descripción</label>
              <p class="mt-1 text-gray-700 text-sm">${proj.description}</p>
            </div>` : ''}
            ${proj.observaciones ? `
            <div class="bg-gray-50 rounded-xl p-4">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Observaciones</label>
              <p class="mt-1 text-gray-700 text-sm">${proj.observaciones}</p>
            </div>` : ''}
            <div class="flex justify-end gap-3 pt-2">
              <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors">Cerrar</button>
              <button onclick="irADocumentos(${projectId}); this.closest('.fixed').remove()" class="bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-4 py-2 font-medium transition-colors text-sm">Ir a Documentos</button>
            </div>
          </div>
        </div>`;
      document.body.appendChild(modal);
    } catch (e) {
      alert('Error al cargar detalle del proyecto: ' + e.message);
    }
  };

  window.irADocumentos = function(projectId) {
    const rol = getRol();
    const basePath = '/r/' + rol;
    const docsPath = rol === 'superadmin' ? basePath + '/documentos?project_id=' : basePath + '/documentos?project_id=';
    const autorPath = '/r/autor/documentos?project_id=';
    window.location.href = (rol === 'autor' || rol === 'cliente') ? autorPath + projectId : docsPath + projectId;
  };

  window.filtrarProyectos = function() {
    const input = document.getElementById('filtroNombre');
    if (!input) return;
    const texto = input.value.toLowerCase();
    const tabla = document.querySelector('#tablaProyectos table');
    if (!tabla) return;
    const filas = tabla.querySelectorAll('tbody tr');
    filas.forEach(f => {
      const nombre = f.cells[1] ? f.cells[1].textContent.toLowerCase() : '';
      f.style.display = texto && !nombre.includes(texto) ? 'none' : '';
    });
  };

})();
