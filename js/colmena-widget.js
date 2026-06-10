// Agentic OS Colmena Widget v5.0 - Inyectable en todos los roles
(function() {
    'use strict';

    // Detectar rol desde la URL
    var pathParts = window.location.pathname.split('/');
    var currentRole = 'registrado';
    for (var i = 0; i < pathParts.length; i++) {
        var knownRoles = ['superadmin','admin','autor','coordinador','cliente','abogado','revisor-qa','ingeniero-lms','editor','guionista','animador-2d','animador-3d','disenador-grafico','disenador-instruccional','desarrollador-multimedia','corrector-de-estilo','video','gerente-general','registrado'];
        if (knownRoles.indexOf(pathParts[i]) !== -1) {
            currentRole = pathParts[i];
            break;
        }
    }

    var jwtToken = sessionStorage.getItem('token') || localStorage.getItem('token') || '';
    var rawSecret = 'CODE_SIGNING_HMAC_ADN_PROTECTED_KEY_9999X_ETHICAL';

    // Estilos CSS del widget
    var style = document.createElement('style');
    style.innerHTML = `
        .agentic-widget-container { position: fixed; bottom: 20px; right: 20px; z-index: 99999; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .agentic-btn { width: 56px; height: 56px; border-radius: 50%; background: #0f172a; border: 2px solid #38bdf8; cursor: pointer; color: #38bdf8; font-size: 22px; display: flex; align-items: center; justify-content: center; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
        .agentic-btn:hover { transform: scale(1.08); box-shadow: 0 0 20px rgba(56,189,248,0.3); }
        .agentic-panel { display: none; width: 360px; height: 480px; background: #1e293b; border: 1px solid #334155; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.7); flex-direction: column; overflow: hidden; margin-bottom: 10px; }
        .agentic-panel.open { display: flex; }
        .agentic-header { background: #0f172a; padding: 14px 16px; color: #38bdf8; font-weight: 600; font-size: 13px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .agentic-header .role-badge { font-size: 10px; background: #38bdf8; color: #0f172a; padding: 2px 10px; border-radius: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .agentic-log { flex: 1; padding: 16px; overflow-y: auto; color: #cbd5e1; font-size: 13px; background: #0f172a; border-bottom: 1px solid #334155; line-height: 1.6; }
        .agentic-log .log-entry { margin-bottom: 6px; }
        .agentic-log .log-user { color: #94a3b8; }
        .agentic-log .log-agent { color: #34d399; }
        .agentic-log .log-system { color: #f43f5e; font-size: 12px; }
        .agentic-log .log-info { color: #38bdf8; }
        .agentic-input-container { display: flex; background: #0f172a; padding: 8px; gap: 6px; }
        .agentic-input { flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; color: #f8fafc; font-size: 13px; outline: none; }
        .agentic-input:focus { border-color: #38bdf8; }
        .agentic-input::placeholder { color: #64748b; }
        .agentic-send-btn { background: #38bdf8; border: none; border-radius: 8px; color: #0f172a; padding: 8px 14px; cursor: pointer; font-weight: 700; font-size: 13px; }
        .agentic-send-btn:hover { background: #7dd3fc; }
        .degrade-visual-effects * { transition: none !important; animation: none !important; text-shadow: none !important; box-shadow: none !important; }
    `;
    document.head.appendChild(style);

    function initWidget() {
        // Construir widget DOM
        var container = document.createElement('div');
        container.className = 'agentic-widget-container';

        var panel = document.createElement('div');
        panel.className = 'agentic-panel';
        panel.id = 'agenticPanel';
        panel.innerHTML = `
            <div class="agentic-header">
                <span>🤖 COLMENA OS</span>
                <span class="role-badge">${currentRole}</span>
            </div>
            <div class="agentic-log" id="agenticLog">
                <div class="log-entry log-info">🟢 Colmena Agentic OS inicializado para <strong>${currentRole}</strong></div>
                <div class="log-entry log-info">🔐 Canal cifrado AES-GCM</div>
            </div>
            <div class="agentic-input-container">
                <input type="text" class="agentic-input" id="agenticInput" placeholder="Comando en lenguaje natural...">
                <button class="agentic-send-btn" id="agenticSend">→</button>
            </div>
        `;

        var btn = document.createElement('button');
        btn.className = 'agentic-btn';
        btn.id = 'agenticToggleBtn';
        btn.innerHTML = '🐝';
        btn.title = 'Abrir Colmena Agentic OS';

        container.appendChild(panel);
        container.appendChild(btn);
        document.body.appendChild(container);

        var logContainer = document.getElementById('agenticLog');
        var inputField = document.getElementById('agenticInput');
        var sendBtn = document.getElementById('agenticSend');
        var panelEl = document.getElementById('agenticPanel');
        var toggleBtn = document.getElementById('agenticToggleBtn');

    var ws = null;
    var cryptoKey = null;
    var isConnected = false;
    var reconnectTimer = null;

    function log(message, type) {
        var cls = type === 'user' ? 'log-user' : type === 'agent' ? 'log-agent' : type === 'system' ? 'log-system' : 'log-info';
        logContainer.innerHTML += '<div class="log-entry ' + cls + '">' + message + '</div>';
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // Crypto functions using Web Crypto API
    async function getCryptoKey(rawKey) {
        var encoder = new TextEncoder();
        var keyData = encoder.encode(rawKey);
        var hash = await window.crypto.subtle.digest('SHA-256', keyData);
        return await window.crypto.subtle.importKey('raw', hash, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
    }

    async function decryptMessage(cipherBase64, key) {
        var binaryStr = atob(cipherBase64);
        var combined = new Uint8Array(binaryStr.length);
        for (var i = 0; i < binaryStr.length; i++) combined[i] = binaryStr.charCodeAt(i);
        var iv = combined.slice(0, 12);
        var ciphertext = combined.slice(12);
        var decrypted = await window.crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, ciphertext);
        return new TextDecoder().decode(decrypted);
    }

    async function encryptMessage(plainText, key) {
        var encoder = new TextEncoder();
        var iv = window.crypto.getRandomValues(new Uint8Array(12));
        var encrypted = await window.crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, key, encoder.encode(plainText));
        var combined = new Uint8Array(iv.length + encrypted.byteLength);
        combined.set(iv, 0);
        combined.set(new Uint8Array(encrypted), iv.length);
        var binary = '';
        for (var i = 0; i < combined.length; i++) binary += String.fromCharCode(combined[i]);
        return btoa(binary);
    }

    function connectWebSocket() {
        if (ws && ws.readyState === WebSocket.OPEN) return;
        var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        var host = window.location.host;
        var wsUrl = protocol + '//' + host + '/ws/agent/' + currentRole + '?token=' + encodeURIComponent(jwtToken);

        try {
            ws = new WebSocket(wsUrl);
        } catch (e) {
            log('🔴 Error de conexión WebSocket', 'system');
            return;
        }

        ws.onopen = function() {
            isConnected = true;
            log('🟢 Conectado a Colmena OS', 'info');
            if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
        };

        ws.onclose = function() {
            isConnected = false;
            log('🔴 Desconectado. Reconectando en 5s...', 'system');
            reconnectTimer = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = function() {
            log('🔴 Error de conexión', 'system');
        };

        ws.onmessage = async function(event) {
            try {
                if (!cryptoKey) return;
                var decrypted = await decryptMessage(event.data, cryptoKey);
                var payload = JSON.parse(decrypted);

                if (payload.type === 'security_alert') {
                    log('⚠️ ' + payload.message, 'system');
                } else if (payload.type === 'system_action' && payload.action === 'degrade_ui') {
                    log('🔥 CPU/RAM crítica. Degradando UI...', 'system');
                    document.body.classList.add('degrade-visual-effects');
                } else if (payload.type === 'recovery_event') {
                    log('🩹 ' + payload.message, 'system');
                } else if (payload.type === 'ui_component') {
                    log('🤖 ' + (payload.data.message || 'Comando procesado'), 'agent');
                } else if (payload.status === 'sinapsis_hibernada') {
                    log('💤 Sesión hibernada (ahorro de RAM)', 'info');
                } else if (payload.status === 'sinapsis_activa') {
                    log('⚡ Sesión restaurada', 'info');
                } else if (payload.type === 'telemetry') {
                    var t = payload.data;
                    log('📊 CPU: ' + t.cpu_percent + '% | RAM: ' + t.ram_percent + '%', 'info');
                } else if (payload.type === 'query_result') {
                    log('📋 ' + payload.entity_type + ': ' + payload.count + ' resultados', 'agent');
                    if (payload.formatted) {
                        payload.formatted.split('\n').forEach(function(line) { log(line, 'info'); });
                    } else if (payload.data && payload.data.length > 0) {
                        var preview = JSON.stringify(payload.data[0]).substring(0, 120);
                        log('   Ej: ' + preview, 'info');
                    }
                } else if (payload.type === 'mutate_result') {
                    if (payload.formatted) { log(payload.formatted, 'agent'); }
                    else { log('✏️ ' + payload.action + ' en ' + payload.entity_type + ' exitoso', 'agent'); }
                } else if (payload.type === 'background_started') {
                    log('⏳ ' + payload.message, 'info');
                } else if (payload.type === 'background_complete') {
                    if (payload.status === 'success') {
                        log('✅ ' + payload.message, 'agent');
                        if (payload.data && typeof payload.data === 'string') {
                            log('   ' + payload.data.substring(0, 200), 'info');
                        }
                    } else {
                        log('❌ ' + payload.message, 'system');
                    }
                } else if (payload.type === 'intent_unknown') {
                    log('🤔 ' + payload.message, 'system');
                } else {
                    log('📨 ' + JSON.stringify(payload).substring(0, 200), 'info');
                }
            } catch (err) {
                console.error('Colmena decrypt error:', err);
            }
        };
    }

    async function sendCommand(cmd) {
        if (!cmd.trim()) return;
        if (!cryptoKey) {
            log('🔑 Inicializando cifrado...', 'info');
            cryptoKey = await getCryptoKey(rawSecret);
        }
        if (!isConnected) {
            log('⚠️ No conectado. Intentando reconectar...', 'system');
            connectWebSocket();
            log('👤 ' + cmd, 'user');
            return;
        }
        log('👤 ' + cmd, 'user');
        try {
            var payload = JSON.stringify({ action: 'execute_command', command: cmd });
            var encrypted = await encryptMessage(payload, cryptoKey);
            ws.send(encrypted);
        } catch (e) {
            log('🔴 Error al enviar comando', 'system');
        }
    }

    // Eventos de UI
    toggleBtn.onclick = function() {
        var isOpen = panelEl.classList.toggle('open');
        toggleBtn.innerHTML = isOpen ? '✕' : '🐝';
        if (isOpen) {
            logContainer.scrollTop = logContainer.scrollHeight;
            if (!cryptoKey) {
                getCryptoKey(rawSecret).then(function(k) {
                    cryptoKey = k;
                    connectWebSocket();
                });
            } else if (!isConnected) {
                connectWebSocket();
            }
        }
    };

    inputField.onkeydown = function(e) {
        if (e.key === 'Enter') { sendCommand(inputField.value); inputField.value = ''; }
    };
    sendBtn.onclick = function() { sendCommand(inputField.value); inputField.value = ''; };

    // Hibernación sináptica por foco de pestaña
    window.addEventListener('blur', async function() {
        if (cryptoKey && isConnected) {
            var payload = JSON.stringify({ action: 'page_blur', role: currentRole });
            ws.send(await encryptMessage(payload, cryptoKey));
        }
    });
    window.addEventListener('focus', async function() {
        if (cryptoKey && isConnected) {
            var payload = JSON.stringify({ action: 'page_focus', role: currentRole });
            ws.send(await encryptMessage(payload, cryptoKey));
        }
    });

        log('🐝 Colmena Agentic OS v5.0 cargado', 'info');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidget);
    } else {
        initWidget();
    }

})();
