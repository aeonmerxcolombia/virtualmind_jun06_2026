const API_VENCIMIENTO = "https://gestordecursos.pegui.edu.co:8000";

function getVencimientoBadge(tarea) {
    if (!tarea.fecha_entrega) return '<span class="text-xs text-gray-400">Sin fecha</span>';

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const entrega = new Date(tarea.fecha_entrega + 'T00:00:00');
    const diffTime = entrega - hoy;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (tarea.estado === 'Cerrado' || tarea.estado === 'Resuelto') {
        return '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Completada</span>';
    }

    if (diffDays < 0) {
        const daysLate = Math.abs(diffDays);
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 animate-pulse">🔴 Vencido (${daysLate}d)</span>`;
    }

    if (diffDays === 0) {
        return '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 font-bold">🟠 Vence hoy</span>';
    }

    if (diffDays <= 2) {
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">🟡 Vence en ${diffDays}d</span>`;
    }

    if (diffDays <= 7) {
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">🔵 Vence en ${diffDays}d</span>`;
    }

    return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">${diffDays}d</span>`;
}

function getVencimientoModalSection(tarea) {
    if (!tarea.fecha_entrega) return '';

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const entrega = new Date(tarea.fecha_entrega + 'T00:00:00');
    const diffTime = entrega - hoy;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    let color = 'bg-green-50 border-green-300 text-green-800';
    let icon = '✅';
    let mensaje = `Quedan ${diffDays} días`;

    if (tarea.estado === 'Cerrado' || tarea.estado === 'Resuelto') {
        color = 'bg-gray-50 border-gray-300 text-gray-600';
        icon = '✅';
        mensaje = 'Tarea completada';
    } else if (diffDays < 0) {
        color = 'bg-red-50 border-red-300 text-red-700';
        icon = '🔴';
        mensaje = `Vencida hace ${Math.abs(diffDays)} día(s)`;
    } else if (diffDays === 0) {
        color = 'bg-orange-50 border-orange-300 text-orange-700';
        icon = '🟠';
        mensaje = 'Vence hoy';
    } else if (diffDays <= 2) {
        color = 'bg-yellow-50 border-yellow-300 text-yellow-800';
        icon = '🟡';
        mensaje = `Vence en ${diffDays} día(s)`;
    }

    const mostrarBoton = tarea.estado !== 'Cerrado' && tarea.estado !== 'Resuelto';

    return `
        <div class="bg-gray-50 rounded-xl p-4 border ${color}">
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-semibold text-gray-600 mb-1">Estado de vencimiento</label>
                    <p class="text-sm font-medium">${icon} ${mensaje} (${tarea.fecha_entrega})</p>
                </div>
                ${mostrarBoton ? `
                <button onclick="abrirModalAmpliacion(${tarea.id})"
                    class="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all transform hover:scale-105">
                    📅 Solicitar ampliación
                </button>
                ` : ''}
            </div>
        </div>
    `;
}

function abrirModalAmpliacion(tareaId) {
    const token = localStorage.getItem('token');
    if (!token) { alert('Debes iniciar sesión'); return; }

    // Obtener datos de la tarea
    fetch(`${API_VENCIMIENTO}/tareas/${tareaId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(tarea => {
        mostrarModalAmpliacion(tarea);
    })
    .catch(err => {
        console.error('Error obteniendo tarea:', err);
        alert('Error al obtener datos de la tarea');
    });
}

function mostrarModalAmpliacion(tarea) {
    const hoy = new Date().toISOString().split('T')[0];
    const fechaActual = tarea.fecha_entrega || hoy;

    const modalHtml = `
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-fade-in" id="modalAmpliacion">
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto animate-bounce-in">
                <div class="sticky top-0 bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6 rounded-t-2xl">
                    <div class="flex justify-between items-center">
                        <div class="flex items-center space-x-3">
                            <div class="bg-white/20 rounded-lg p-2">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                            <h2 class="text-2xl font-bold">Solicitar ampliación</h2>
                        </div>
                        <button class="bg-white/20 hover:bg-white/30 rounded-lg p-2 transition-colors" onclick="cerrarModalAmpliacion()">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="p-6 space-y-6">
                    <div class="bg-orange-50 border border-orange-200 rounded-xl p-4">
                        <p class="text-sm text-orange-800">
                            <strong>Tarea:</strong> ${tarea.titulo}<br>
                            <strong>Fecha actual de entrega:</strong> ${fechaActual}
                        </p>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Nueva fecha de entrega *</label>
                        <input type="date" id="nuevaFechaAmpliacion" min="${hoy}" value="${fechaActual}"
                            class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Razón de la ampliación *</label>
                        <textarea id="razonAmpliacion" rows="4"
                            class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            placeholder="Explica detalladamente por qué necesitas más tiempo..."></textarea>
                    </div>
                    <button onclick="enviarSolicitudAmpliacion(${tarea.id})"
                        class="w-full bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-bold py-3 px-6 rounded-lg transition-all transform hover:scale-[1.02]">
                        📤 Enviar solicitud
                    </button>
                </div>
            </div>
        </div>
    `;

    const container = document.getElementById('modal-container') || document.body;
    const div = document.createElement('div');
    div.innerHTML = modalHtml;
    container.appendChild(div.firstElementChild);
}

function cerrarModalAmpliacion() {
    const modal = document.getElementById('modalAmpliacion');
    if (modal) modal.remove();
}

function enviarSolicitudAmpliacion(tareaId) {
    const nuevaFecha = document.getElementById('nuevaFechaAmpliacion').value;
    const razon = document.getElementById('razonAmpliacion').value.trim();
    const token = localStorage.getItem('token');

    if (!nuevaFecha) { alert('Selecciona una nueva fecha'); return; }
    if (!razon) { alert('Escribe la razón de la ampliación'); return; }
    if (razon.length < 20) { alert('La razón debe tener al menos 20 caracteres'); return; }

    const formData = new URLSearchParams();
    formData.append('fecha_solicitada', nuevaFecha);
    formData.append('razon', razon);

    fetch(`${API_VENCIMIENTO}/tareas/${tareaId}/solicitar-ampliacion`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    })
    .then(async res => {
        const data = await res.json();
        if (res.ok) {
            cerrarModalAmpliacion();
            alert('✅ Solicitud enviada correctamente. Un administrador revisará tu petición.');
        } else {
            alert(`Error: ${data.detail || 'No se pudo enviar la solicitud'}`);
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('Error de conexión al enviar la solicitud');
    });
}
