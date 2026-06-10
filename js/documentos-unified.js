(function () {
    const API_URL = 'https://gestordecursos.pegui.edu.co:8000';
    let jitsiInstance = null;
    let chatDestinatario = null;

    function getToken() {
        return localStorage.getItem('token') || sessionStorage.getItem('token');
    }

    function apiFetch(path, options = {}) {
        const headers = { ...options.headers };
        const token = getToken();
        if (token) headers['Authorization'] = 'Bearer ' + token;
        return fetch(API_URL + path, { ...options, headers });
    }

    // ============ VIDEOLLAMADA ============

    window.mostrarVideollamada = function () {
        document.getElementById('subirArchivos').classList.add('d-none');
        document.getElementById('compartidosSection').classList.add('d-none');
        document.getElementById('documentos-lista').classList.add('d-none');
        document.getElementById('seccionChat').classList.add('d-none');
        document.getElementById('seccionRevisiones').classList.add('d-none');
        document.getElementById('seccionVideollamada').classList.remove('d-none');
        document.querySelectorAll('#docTabs .nav-link').forEach(t => t.classList.remove('active'));
        document.getElementById('tab-videollamada').classList.add('active');
    };

    window.iniciarVideollamada = async function () {
        const sala = document.getElementById('salaNombre').value.trim();
        if (!sala) { alert('Ingresa un nombre para la sala'); return; }

        const container = document.getElementById('jitsiContainer');
        container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Conectando con Jitsi Meet...</p></div>';
        container.classList.remove('d-none');

        if (jitsiInstance) { jitsiInstance.dispose(); jitsiInstance = null; }

        if (typeof JitsiMeetExternalAPI === 'undefined') {
            await new Promise((resolve, reject) => {
                const s = document.createElement('script');
                s.src = 'https://meet.jit.si/external_api.js';
                s.onload = resolve;
                s.onerror = reject;
                document.head.appendChild(s);
            });
        }

        const token = getToken();
        let nombre = 'Usuario';
        if (token) {
            try {
                const parts = token.split('.');
                if (parts.length === 3) {
                    const payload = JSON.parse(atob(parts[1]));
                    nombre = payload.name || payload.sub || 'Usuario';
                }
            } catch (e) {}
        }

        jitsiInstance = new JitsiMeetExternalAPI('meet.jit.si', {
            roomName: sala,
            width: '100%',
            height: 500,
            parentNode: container,
            userInfo: { displayName: nombre }
        });

        document.getElementById('jitsiControls').classList.remove('d-none');
    };

    window.colgarVideollamada = function () {
        if (jitsiInstance) { jitsiInstance.dispose(); jitsiInstance = null; }
        document.getElementById('jitsiContainer').innerHTML = '';
        document.getElementById('jitsiContainer').classList.add('d-none');
        document.getElementById('jitsiControls').classList.add('d-none');
    };

    // ============ CHAT ============

    async function cargarUsuariosProyecto() {
        const projectId = new URLSearchParams(window.location.search).get('project_id');
        if (!projectId) return [];

        try {
            const res = await apiFetch('/tareas/?project_id=' + projectId);
            if (!res.ok) return [];
            const tareas = await res.json();

            const uids = new Set();
            tareas.forEach(t => {
                if (t.asignado) uids.add(t.asignado);
                if (t.usuario_id) uids.add(t.usuario_id);
            });

            const users = [];
            for (const uid of uids) {
                try {
                    const r = await apiFetch('/users/' + uid);
                    if (r.ok) {
                        const u = await r.json();
                        users.push({ uid, nombre: u.name || u.nombre || uid, email: u.email || '' });
                    } else {
                        users.push({ uid, nombre: uid, email: '' });
                    }
                } catch (e) {
                    users.push({ uid, nombre: uid, email: '' });
                }
            }
            return users;
        } catch (e) {
            return [];
        }
    }

    window.mostrarChat = async function () {
        document.getElementById('subirArchivos').classList.add('d-none');
        document.getElementById('compartidosSection').classList.add('d-none');
        document.getElementById('documentos-lista').classList.add('d-none');
        document.getElementById('seccionVideollamada').classList.add('d-none');
        document.getElementById('seccionRevisiones').classList.add('d-none');
        document.getElementById('seccionChat').classList.remove('d-none');
        document.querySelectorAll('#docTabs .nav-link').forEach(t => t.classList.remove('active'));
        document.getElementById('tab-chat').classList.add('active');

        const lista = document.getElementById('chatParticipantes');
        lista.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Cargando participantes...</div>';

        const users = await cargarUsuariosProyecto();
        if (!users.length) {
            lista.innerHTML = '<div class="text-center py-4 text-muted">No hay participantes en este proyecto</div>';
            return;
        }

        lista.innerHTML = users.map(u => `
            <div class="d-flex align-items-center gap-2 p-2 border-bottom chat-user-item" style="cursor:pointer" onclick="seleccionarChatParticipante('${u.uid}', '${u.nombre}')">
                <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center" style="width:36px;height:36px;font-size:14px;flex-shrink:0">
                    ${u.nombre.charAt(0).toUpperCase()}
                </div>
                <div class="flex-grow-1 min-w-0">
                    <div class="fw-medium text-truncate">${u.nombre}</div>
                    <small class="text-muted text-truncate d-block">${u.email}</small>
                </div>
            </div>
        `).join('');
    };

    window.seleccionarChatParticipante = function (uid, nombre) {
        chatDestinatario = { uid, nombre };
        document.getElementById('chatHeader').innerHTML = `
            <i class="fas fa-comment me-2"></i> Chat con: <strong>${nombre}</strong>
            <button class="btn btn-sm btn-outline-secondary ms-auto" onclick="volverListaParticipantes()" title="Volver a lista de participantes">
                <i class="fas fa-users"></i>
            </button>
        `;
        document.getElementById('chatParticipantes').classList.add('d-none');
        document.getElementById('chatConversacion').classList.remove('d-none');
        document.getElementById('chatMensajes').innerHTML = '<div class="text-center py-4 text-muted">Cargando mensajes...</div>';
        document.getElementById('chatInputArea').classList.remove('d-none');
        cargarConversacion(uid);
    };

    window.volverListaParticipantes = function () {
        chatDestinatario = null;
        document.getElementById('chatParticipantes').classList.remove('d-none');
        document.getElementById('chatConversacion').classList.add('d-none');
        document.getElementById('chatInputArea').classList.add('d-none');
        document.getElementById('chatHeader').innerHTML = '<i class="fas fa-comments me-2"></i> Participantes del Proyecto';
    };

    async function cargarConversacion(otroUid) {
        try {
            const res = await apiFetch('/mensajes/conversacion/' + otroUid);
            if (!res.ok) throw new Error();
            const msgs = await res.json();
            const container = document.getElementById('chatMensajes');

            const miUid = await obtenerMiUid();
            if (!msgs.length) {
                container.innerHTML = '<div class="text-center py-5 text-muted"><i class="fas fa-inbox fa-3x mb-3 d-block"></i>No hay mensajes aún. ¡Envía el primero!</div>';
                return;
            }
            container.innerHTML = msgs.map(m => `
                <div class="mb-2 d-flex ${m.remitente_uid === miUid ? 'justify-content-end' : ''}">
                    <div class="p-2 rounded-3 ${m.remitente_uid === miUid ? 'bg-primary text-white' : 'bg-light'}" style="max-width:80%">
                        <div class="small">${m.contenido}</div>
                        <div class="small opacity-50 mt-1" style="font-size:10px">${new Date(m.timestamp).toLocaleTimeString()}</div>
                    </div>
                </div>
            `).join('');
            container.scrollTop = container.scrollHeight;
        } catch (e) {
            document.getElementById('chatMensajes').innerHTML = '<div class="text-center py-4 text-danger">Error al cargar mensajes</div>';
        }
    }

    let miUidCache = null;
    async function obtenerMiUid() {
        if (miUidCache) return miUidCache;
        try {
            const token = getToken();
            if (!token) return null;
            const parts = token.split('.');
            if (parts.length === 3) {
                const payload = JSON.parse(atob(parts[1]));
                miUidCache = payload.user_id || payload.sub;
                return miUidCache;
            }
        } catch (e) {}
        return null;
    }

    window.enviarMensajeChat = async function () {
        const input = document.getElementById('chatInput');
        const texto = input.value.trim();
        if (!texto || !chatDestinatario) return;

        const btn = document.getElementById('btnEnviarChat');
        btn.disabled = true;

        try {
            const res = await apiFetch('/mensajes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contenido: texto,
                    destinatario_uid: chatDestinatario.uid
                })
            });

            if (res.ok) {
                input.value = '';
                await cargarConversacion(chatDestinatario.uid);
            } else {
                alert('Error al enviar mensaje');
            }
        } catch (e) {
            alert('Error de conexión');
        }
        btn.disabled = false;
    };

    window.adjuntarDocumentoChat = async function () {
        if (!chatDestinatario) { alert('Selecciona un participante primero'); return; }

        const docs = window.archivos || [];
        if (!docs.length) { alert('No hay documentos en este proyecto'); return; }

        const nombres = docs.map((d, i) => `${i + 1}. ${d.nombre}.${d.tipo}`).join('\n');
        const seleccion = prompt('Selecciona el número del documento a compartir:\n' + nombres);
        if (!seleccion) return;

        const idx = parseInt(seleccion) - 1;
        if (isNaN(idx) || idx < 0 || idx >= docs.length) { alert('Selección inválida'); return; }

        const doc = docs[idx];
        const link = `${API_URL}/documentos-office/info/${doc.id}`;
        const texto = `📎 Te comparto el documento: ${doc.nombre}.${doc.tipo}\n${link}`;

        try {
            const res = await apiFetch('/mensajes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contenido: texto, destinatario_uid: chatDestinatario.uid })
            });

            if (res.ok) {
                await cargarConversacion(chatDestinatario.uid);
            }
        } catch (e) {
            alert('Error al compartir documento');
        }
    };

    // Enter para enviar
    document.addEventListener('DOMContentLoaded', function () {
        const input = document.getElementById('chatInput');
        if (input) {
            input.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') enviarMensajeChat();
            });
        }
    });

})();
