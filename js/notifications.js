// notifications.js - Manejo inteligente de notificaciones clickeables
// Requiere: API (URL base), token válido, getToken() definido

async function cargarNotificacionesInteligentes(notifButton, notifList, notifCount, notifEmpty) {
    try {
        const res = await fetch(`${API}/notifications/`, {
            headers: { 'Authorization': 'Bearer ' + getToken() }
        });
        if (res.status === 401) { logout(); return; }
        
        const data = await res.json();
        const user_id = localStorage.getItem("user_id");
        const notifs = (data.notificaciones || []).filter(n => String(n.usuario_id) === String(user_id));
        
        notifList.innerHTML = "";
        
        if (notifs.length === 0) {
            notifCount.textContent = 0;
            notifEmpty.style.display = "block";
            notifButton.querySelector('span')?.classList.add('hidden');
            return;
        }
        
        notifCount.textContent = notifs.length;
        notifEmpty.style.display = "none";
        notifButton.querySelector('span')?.classList.remove('hidden');
        
        notifs.forEach(n => {
            const div = document.createElement("div");
            div.className = "px-4 py-3 hover:bg-gray-700 cursor-pointer text-sm border-bottom border-gray-600 transition";
            div.style.cssText = "background-color: #1f2937; color: #f9fafb;";
            
            const fecha = new Date(n.fecha).toLocaleString('es-ES', {
                day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
            });
            
            div.innerHTML = `
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <p style="color: #f9fafb; font-weight: 500;">${n.descripcion}</p>
                        <small style="color: #9ca3af;">${fecha}</small>
                    </div>
                    ${n.link ? '<i class="fas fa-external-link-alt" style="color: #6366f1; margin-left: 8px;"></i>' : ''}
                </div>
            `;
            
            // Hacer clickeable si tiene link
            if (n.link) {
                div.onclick = () => {
                    const currentRole = window.location.pathname.match(/\/r\/([^/]+)/);
                    if (currentRole && n.link.includes('/r/')) {
                        const link = n.link.replace(/\/r\/[^/]+/, '/r/' + currentRole[1]);
                        window.location.href = link;
                    } else {
                        window.location.href = n.link;
                    }
                };
                div.title = "Hacer clic para ir al documento/proyecto";
            } else {
                div.style.cursor = "default";
                div.onclick = () => {
                    // Si no tiene link, marcar como leída
                    fetch(`${API}/notifications/leer`, {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + getToken() }
                    }).then(() => cargarNotificacionesInteligentes(notifButton, notifList, notifCount, notifEmpty));
                };
            }
            
            notifList.appendChild(div);
        });
    } catch (err) {
        console.error("Error cargando notificaciones:", err);
    }
}

// Función para mostrar notificación tipo toast (para documentos compartidos, etc.)
function mostrarNotificacionInteligente(tipo, titulo, mensaje, link = null) {
    let colorBg, colorBorder, icono;
    switch(tipo) {
        case 'success':
            colorBg = 'bg-green-500';
            icono = 'fa-check-circle';
            break;
        case 'error':
            colorBg = 'bg-red-500';
            icono = 'fa-times-circle';
            break;
        case 'info':
        default:
            colorBg = 'bg-blue-500';
            icono = 'fa-info-circle';
    }
    
    const notifDiv = document.createElement('div');
    notifDiv.className = `${colorBg} text-white shadow-lg rounded-lg px-4 py-3 mb-3 flex items-center`;
    notifDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 320px; max-width: 400px; cursor: pointer; transition: all 0.3s;';
    
    notifDiv.innerHTML = `
        <i class="fas ${icono} me-3 text-xl"></i>
        <div class="flex-1">
            <strong class="block">${titulo}</strong>
            <span class="text-sm opacity-90">${mensaje}</span>
            ${link ? '<small class="block mt-1 opacity-75"><i class="fas fa-link me-1"></i>Hacer clic para abrir</small>' : ''}
        </div>
        <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.remove()"></button>
    `;
    
    // Click en toda la notificación
    if (link) {
        notifDiv.onclick = (e) => {
            if (!e.target.classList.contains('btn-close')) {
                const currentRole = window.location.pathname.match(/\/r\/([^/]+)/);
                let finalLink = link;
                if (currentRole && link.includes('/r/')) {
                    finalLink = link.replace(/\/r\/[^/]+/, '/r/' + currentRole[1]);
                }
                window.location.href = finalLink;
            }
        };
    }
    
    document.body.appendChild(notifDiv);
    setTimeout(() => {
        notifDiv.style.opacity = '0';
        notifDiv.style.transform = 'translateX(100px)';
        setTimeout(() => notifDiv.remove(), 300);
    }, 8000);
}

// Exportar funciones para uso global
if (typeof window !== 'undefined') {
    window.cargarNotificacionesInteligentes = cargarNotificacionesInteligentes;
    window.mostrarNotificacionInteligente = mostrarNotificacionInteligente;
}
