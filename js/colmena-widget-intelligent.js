(function () {
  'use strict';

  function initWidget() {
  var pathParts = window.location.pathname.split('/');
  var currentRole = 'registrado';
  var knownRoles = [
    'superadmin', 'admin', 'autor', 'coordinador', 'cliente', 'abogado',
    'revisor-qa', 'ingeniero-lms', 'editor', 'guionista', 'animador-2d',
    'animador-3d', 'disenador-grafico', 'disenador-instruccional',
    'desarrollador-multimedia', 'corrector-de-estilo', 'video',
    'gerente-general', 'registrado'
  ];
  for (var i = 0; i < pathParts.length; i++) {
    if (knownRoles.indexOf(pathParts[i]) !== -1) {
      currentRole = pathParts[i];
      break;
    }
  }

  var jwtToken = sessionStorage.getItem('token') || localStorage.getItem('token') || '';
  var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  var host = window.location.host;
  var baseUrl = window.location.protocol + '//' + host;

  var state = {
    ws: null,
    cryptoKey: null,
    isConnected: false,
    reconnectTimer: null,
    history: [],
    historyIdx: -1,
    isProcessing: false,
    mode: 'auto',
    contextId: 'colmena_' + Math.random().toString(36).slice(2, 10),
  };

  var style = document.createElement('style');
  style.innerHTML = [
    '.colmena-widget * { box-sizing: border-box; }',
    '.colmena-widget { position: fixed; bottom: 20px; right: 20px; z-index: 99999; font-family: "Segoe UI",system-ui,sans-serif; }',
    '.colmena-toggle { width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg,#0f172a,#1e293b); border: 2px solid #38bdf8; cursor: pointer; color: #38bdf8; font-size: 22px; display: flex; align-items: center; justify-content: center; transition: all 0.3s; box-shadow: 0 4px 16px rgba(0,0,0,0.5); position: relative; }',
    '.colmena-toggle:hover { transform: scale(1.1); box-shadow: 0 0 30px rgba(56,189,248,0.3); }',
    '.colmena-toggle .badge-dot { position: absolute; top: 2px; right: 2px; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; border: 2px solid #0f172a; }',
    '.colmena-toggle .badge-dot.disconnected { background: #ef4444; }',
    '.colmena-panel { display: none; width: 400px; height: 540px; background: #0f172a; border: 1px solid #1e293b; border-radius: 16px; box-shadow: 0 8px 40px rgba(0,0,0,0.8); flex-direction: column; overflow: hidden; margin-bottom: 10px; border: 1px solid #38bdf822; }',
    '.colmena-panel.open { display: flex; }',
    '.colmena-header { background: linear-gradient(135deg,#0f172a,#1a2744); padding: 12px 16px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }',
    '.colmena-header .title { color: #38bdf8; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 8px; }',
    '.colmena-header .title .role-tag { font-size: 9px; background: #38bdf8; color: #0f172a; padding: 2px 10px; border-radius: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }',
    '.colmena-header .title .mode-tag { font-size: 8px; background: #334155; color: #94a3b8; padding: 2px 8px; border-radius: 8px; font-weight: 600; }',
    '.colmena-header .actions { display: flex; gap: 4px; }',
    '.colmena-header .actions button { background: none; border: none; color: #64748b; cursor: pointer; font-size: 14px; padding: 2px 6px; border-radius: 4px; }',
    '.colmena-header .actions button:hover { background: #1e293b; color: #38bdf8; }',
    '.colmena-suggestions { display: flex; gap: 4px; padding: 6px 12px; background: #0c1222; border-bottom: 1px solid #1e293b; overflow-x: auto; flex-shrink: 0; }',
    '.colmena-suggestions::-webkit-scrollbar { height: 2px; }',
    '.colmena-suggestions::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }',
    '.colmena-suggestion-chip { white-space: nowrap; font-size: 10px; padding: 3px 10px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; color: #94a3b8; cursor: pointer; transition: all 0.2s; flex-shrink: 0; }',
    '.colmena-suggestion-chip:hover { background: #38bdf8; color: #0f172a; border-color: #38bdf8; }',
    '.colmena-log { flex: 1; padding: 12px; overflow-y: auto; color: #cbd5e1; font-size: 13px; background: #0a0f1a; line-height: 1.6; display: flex; flex-direction: column; gap: 4px; }',
    '.colmena-log::-webkit-scrollbar { width: 4px; }',
    '.colmena-log::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }',
    '.colmena-msg { padding: 6px 10px; border-radius: 8px; max-width: 90%; animation: fadeIn 0.2s ease; }',
    '.colmena-msg.user { background: #1a2744; color: #e2e8f0; align-self: flex-end; border-bottom-right-radius: 2px; }',
    '.colmena-msg.agent { background: #0f172a; color: #34d399; align-self: flex-start; border-bottom-left-radius: 2px; border-left: 3px solid #34d399; }',
    '.colmena-msg.system { background: #1a1a2e; color: #f43f5e; align-self: flex-start; font-size: 12px; }',
    '.colmena-msg.info { background: #0c1222; color: #38bdf8; align-self: flex-start; font-size: 12px; border-left: 3px solid #38bdf8; }',
    '.colmena-msg .typo-correction { font-size: 11px; color: #fbbf24; display: block; margin-top: 2px; }',
    '.colmena-msg .msg-content { word-break: break-word; }',
    '.colmena-msg .msg-content strong { color: #f8fafc; }',
    '.colmena-msg .msg-content code { background: #1e293b; padding: 1px 4px; border-radius: 3px; font-size: 11px; color: #f472b6; }',
    '.colmena-msg .msg-content pre { background: #1e293b; padding: 8px; border-radius: 6px; overflow-x: auto; font-size: 11px; margin: 4px 0; }',
    '.colmena-input-area { display: flex; gap: 6px; padding: 8px 12px; background: #0f172a; border-top: 1px solid #1e293b; align-items: flex-end; }',
    '.colmena-input-wrap { flex: 1; position: relative; }',
    '.colmena-input { width: 100%; background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; color: #f8fafc; font-size: 13px; outline: none; resize: none; max-height: 80px; line-height: 1.4; }',
    '.colmena-input:focus { border-color: #38bdf8; }',
    '.colmena-input::placeholder { color: #475569; }',
    '.colmena-send-btn { background: linear-gradient(135deg,#38bdf8,#0ea5e9); border: none; border-radius: 10px; color: #0f172a; padding: 10px 16px; cursor: pointer; font-weight: 700; font-size: 13px; transition: all 0.2s; flex-shrink: 0; }',
    '.colmena-send-btn:hover { transform: scale(1.05); }',
    '.colmena-send-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }',
    '.colmena-typing { display: flex; gap: 4px; padding: 4px 0; align-items: center; color: #64748b; font-size: 11px; }',
    '.colmena-typing .dot { width: 6px; height: 6px; background: #38bdf8; border-radius: 50%; animation: pulse 1.4s infinite; }',
    '.colmena-typing .dot:nth-child(2) { animation-delay: 0.2s; }',
    '.colmena-typing .dot:nth-child(3) { animation-delay: 0.4s; }',
    '@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }',
    '@keyframes pulse { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }',
    '.degrade-visual-effects * { transition: none !important; animation: none !important; }',
  ].join('\n');
  document.head.appendChild(style);

  var container = document.createElement('div');
  container.className = 'colmena-widget';

  var panel = document.createElement('div');
  panel.className = 'colmena-panel';
  panel.id = 'colmenaPanel';
  panel.innerHTML = [
    '<div class="colmena-header">',
    '  <div class="title">',
    '    <span>🐝 Colmena OS</span>',
    '    <span class="role-tag">' + currentRole + '</span>',
    '    <span class="mode-tag">INTELIGENTE</span>',
    '  </div>',
    '  <div class="actions">',
    '    <button id="colmenaClear" title="Limpiar">🗑️</button>',
    '  </div>',
    '</div>',
    '<div class="colmena-suggestions" id="colmenaSuggestions"></div>',
    '<div class="colmena-log" id="colmenaLog"></div>',
    '<div class="colmena-input-area">',
    '  <div class="colmena-input-wrap">',
    '    <textarea class="colmena-input" id="colmenaInput" rows="1" placeholder="Escribe en lenguaje natural..."></textarea>',
    '  </div>',
    '  <button class="colmena-send-btn" id="colmenaSend">→</button>',
    '</div>',
  ].join('\n');

  var toggleBtn = document.createElement('button');
  toggleBtn.className = 'colmena-toggle';
  toggleBtn.id = 'colmenaToggle';
  toggleBtn.innerHTML = '🐝<span class="badge-dot disconnected" id="colmenaDot"></span>';
  toggleBtn.title = 'Abrir Colmena Agentic OS';

  container.appendChild(panel);
  container.appendChild(toggleBtn);
  document.body.appendChild(container);

  var logEl = document.getElementById('colmenaLog');
  var inputEl = document.getElementById('colmenaInput');
  var sendBtn = document.getElementById('colmenaSend');
  var panelEl = document.getElementById('colmenaPanel');
  var toggleEl = document.getElementById('colmenaToggle');
  var dotEl = document.getElementById('colmenaDot');
  var suggestionsEl = document.getElementById('colmenaSuggestions');
  var clearBtn = document.getElementById('colmenaClear');

  var suggestions = [];
  var suggestionsByRole = {
    superadmin: ['lista proyectos', 'crea un proyecto', 'lista usuarios', 'diagnóstico', 'telemetría'],
    admin: ['lista proyectos', 'crea un proyecto', 'mis tareas', 'calendario'],
    autor: ['crea un módulo', 'mis unidades', 'mis proyectos', 'biblioteca'],
    coordinador: ['lista proyectos', 'participantes', 'cronograma', 'tareas del proyecto'],
    cliente: ['mis proyectos', 'estado del proyecto', 'documentos'],
    'disenador-instruccional': ['crea un módulo', 'crea una unidad', 'mis diseños', 'plan de estudios'],
    'disenador-grafico': ['mis tareas', 'recursos gráficos', 'proyectos asignados'],
    'desarrollador-multimedia': ['mis tareas', 'recursos multimedia', 'proyectos'],
    editor: ['documentos pendientes', 'mis tareas', 'proyectos'],
    'corrector-de-estilo': ['documentos pendientes', 'mis tareas', 'correcciones'],
    'revisor-qa': ['mis tareas', 'proyectos en revisión', 'reportes'],
    'ingeniero-lms': ['cursos', 'plataforma', 'usuarios', 'configuración'],
    'animador-2d': ['mis tareas', 'animaciones', 'proyectos'],
    'animador-3d': ['mis tareas', 'modelos 3D', 'proyectos'],
    guionista: ['mis guiones', 'proyectos', 'documentos'],
    video: ['mis videos', 'tareas', 'proyectos'],
    abogado: ['documentos legales', 'contratos', 'proyectos'],
    'gerente-general': ['todos los proyectos', 'reportes', 'equipo', 'finanzas'],
    registrado: ['mis proyectos', 'mis tareas', 'perfil'],
  };
  suggestions = suggestionsByRole[currentRole] || suggestionsByRole.registrado;

  function renderSuggestions() {
    if (!suggestionsEl) return;
    suggestionsEl.innerHTML = suggestions.map(function (s) {
      return '<span class="colmena-suggestion-chip" data-cmd="' + s.replace(/"/g, '&quot;') + '">' + s + '</span>';
    }).join('');
    suggestionsEl.querySelectorAll('.colmena-suggestion-chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        sendCommand(this.getAttribute('data-cmd'));
      });
    });
  }
  renderSuggestions();

  function addMsg(text, type, extra) {
    var msg = document.createElement('div');
    msg.className = 'colmena-msg ' + type;
    var html = '<div class="msg-content">' + text + '</div>';
    if (extra && extra.correction) {
      html += '<span class="typo-correction">🔤 Corregido: ' + extra.correction + '</span>';
    }
    msg.innerHTML = html;
    logEl.appendChild(msg);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function showTyping() {
    var t = document.createElement('div');
    t.className = 'colmena-typing';
    t.id = 'colmenaTyping';
    t.innerHTML = '<span>Procesando</span><span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    logEl.appendChild(t);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function hideTyping() {
    var t = document.getElementById('colmenaTyping');
    if (t) t.remove();
  }

  function formatMarkdown(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 80) + 'px';
  }

  function connectWs() {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) return;
    var wsUrl = protocol + '//' + host + '/ws/agent/' + currentRole + '?token=' + encodeURIComponent(jwtToken);
    try { state.ws = new WebSocket(wsUrl); } catch (e) { return; }
    state.ws.onopen = function () {
      state.isConnected = true;
      dotEl.className = 'badge-dot';
      updateModeTag('WS');
    };
    state.ws.onclose = function () {
      state.isConnected = false;
      dotEl.className = 'badge-dot disconnected';
      state.reconnectTimer = setTimeout(connectWs, 5000);
    };
    state.ws.onmessage = async function (event) {
      try {
        if (!state.cryptoKey) return;
        var decrypted = await decryptMessage(event.data, state.cryptoKey);
        var payload = JSON.parse(decrypted);
        hideTyping();
        handleWsPayload(payload);
      } catch (e) { console.error('WS decrypt error', e); }
    };
  }

  function handleWsPayload(p) {
    if (p.type === 'security_alert') { addMsg('⚠️ ' + p.message, 'system'); }
    else if (p.type === 'system_action' && p.action === 'degrade_ui') {
      addMsg('🔥 CPU/RAM crítica. Degradando UI...', 'system');
      document.body.classList.add('degrade-visual-effects');
    } else if (p.type === 'agent_response') {
      addMsg(formatMarkdown(p.message), 'agent');
    } else if (p.type === 'query_result') {
      var h = p.formatted || (p.count + ' resultados encontrados');
      addMsg(formatMarkdown(h), 'agent');
    } else if (p.type === 'mutate_result') {
      addMsg(p.formatted || '✅ Operación exitosa', 'agent');
    } else if (p.type === 'background_started') {
      addMsg('⏳ ' + p.message, 'info');
    } else if (p.type === 'background_complete') {
      addMsg((p.status === 'success' ? '✅ ' : '❌ ') + p.message, p.status === 'success' ? 'agent' : 'system');
    } else if (p.type === 'error') {
      addMsg('❌ ' + p.message, 'system');
    } else if (p.status === 'sinapsis_hibernada') {
      addMsg('💤 Sesión hibernada', 'info');
    } else if (p.status === 'sinapsis_activa') {
      addMsg('⚡ Sesión restaurada', 'info');
    } else if (p.type === 'telemetry') {
      addMsg('📊 CPU: ' + p.data.cpu_percent + '% | RAM: ' + p.data.ram_percent + '%', 'info');
    } else {
      addMsg('📨 ' + JSON.stringify(p).substring(0, 200), 'info');
    }
  }

  async function getCryptoKey(raw) {
    var enc = new TextEncoder();
    var d = enc.encode(raw);
    var h = await window.crypto.subtle.digest('SHA-256', d);
    return window.crypto.subtle.importKey('raw', h, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
  }

  async function decryptMessage(data, key) {
    var bin = atob(data);
    var buf = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
    var iv = buf.slice(0, 12);
    var ct = buf.slice(12);
    var dec = await window.crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, ct);
    return new TextDecoder().decode(dec);
  }

  async function encryptMessage(pt, key) {
    var enc = new TextEncoder();
    var iv = window.crypto.getRandomValues(new Uint8Array(12));
    var e = await window.crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, key, enc.encode(pt));
    var c = new Uint8Array(iv.length + e.byteLength);
    c.set(iv, 0);
    c.set(new Uint8Array(e), iv.length);
    var b = '';
    for (var i = 0; i < c.length; i++) b += String.fromCharCode(c[i]);
    return btoa(b);
  }

  function updateModeTag(mode) {
    var tag = panel.querySelector('.mode-tag');
    if (tag) tag.textContent = mode;
  }

  function getAuthHeaders() {
    return { 'Authorization': 'Bearer ' + jwtToken, 'Content-Type': 'application/json' };
  }

  async function callNlu(text) {
    try {
      var resp = await fetch(baseUrl + '/colmena/nlu', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ text: text, role: currentRole, context_id: state.contextId }),
      });
      if (!resp.ok) return null;
      return await resp.json();
    } catch (e) { return null; }
  }

  async function processViaNlu(text) {
    showTyping();
    var nlu = await callNlu(text);

    if (!nlu) {
      hideTyping();
      addMsg('⚠️ No pude conectar con el NLU. Usando WebSocket...', 'info');
      await sendViaWs(text);
      return;
    }

    hideTyping();

    if (nlu.corrected_text && nlu.corrected_text !== text) {
      addMsg(formatMarkdown(text), 'user', { correction: nlu.corrected_text });
    } else {
      addMsg(formatMarkdown(text), 'user');
    }

    if (nlu.response) {
      addMsg(formatMarkdown(nlu.response), 'agent');
      return;
    }

    addMsg('🤔 No entendí el comando. Sé más específico.', 'system');
  }

  async function sendViaWs(text) {
    if (!state.cryptoKey) {
      state.cryptoKey = await getCryptoKey('CODE_SIGNING_HMAC_ADN_PROTECTED_KEY_9999X_ETHICAL');
    }
    if (!state.isConnected) { connectWs(); }
    if (!state.isConnected) {
      addMsg('⚠️ No conectado. Reintentando...', 'system');
      return;
    }
    var payload = JSON.stringify({ action: 'execute_command', command: text });
    var encrypted = await encryptMessage(payload, state.cryptoKey);
    showTyping();
    state.ws.send(encrypted);
  }

  async function sendCommand(text) {
    text = text.trim();
    if (!text || state.isProcessing) return;
    state.isProcessing = true;
    sendBtn.disabled = true;

    if (!text.match(/^[A-Za-z0-9áéíóúñü\s,.;:!?¡¿"'_@#$%&()+\-=\[\]{}<>\/]+$/)) {
      addMsg('⚠️ El comando contiene caracteres no válidos', 'system');
      state.isProcessing = false;
      sendBtn.disabled = false;
      return;
    }

    if (text.length > 4096) {
      addMsg('⚠️ Texto demasiado largo (máx 4096 caracteres)', 'system');
      state.isProcessing = false;
      sendBtn.disabled = false;
      return;
    }

    state.history.push(text);
    state.historyIdx = state.history.length;

    await processViaNlu(text);

    inputEl.value = '';
    autoResize(inputEl);
    state.isProcessing = false;
    sendBtn.disabled = false;
  }

  function getQuickActions() {
    if (currentRole === 'superadmin' || currentRole === 'admin') {
      return ['📋 Proyectos', '👥 Usuarios', '📊 Diagnóstico', '🔍 Buscar'];
    }
    return ['📋 Mis proyectos', '✅ Mis tareas', '🔍 Buscar'];
  }

  toggleEl.onclick = function () {
    var isOpen = panelEl.classList.toggle('open');
    toggleEl.innerHTML = isOpen ? '✕<span class="badge-dot ' + (state.isConnected ? '' : 'disconnected') + '" id="colmenaDot"></span>' : '🐝<span class="badge-dot ' + (state.isConnected ? '' : 'disconnected') + '" id="colmenaDot"></span>';
    if (isOpen) {
      if (!state.cryptoKey) {
        getCryptoKey('CODE_SIGNING_HMAC_ADN_PROTECTED_KEY_9999X_ETHICAL').then(function (k) {
          state.cryptoKey = k;
          connectWs();
        });
      } else if (!state.isConnected) {
        connectWs();
      }
    }
  };

  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendCommand(inputEl.value);
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (state.historyIdx > 0) {
        state.historyIdx--;
        inputEl.value = state.history[state.historyIdx];
        autoResize(inputEl);
      }
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (state.historyIdx < state.history.length - 1) {
        state.historyIdx++;
        inputEl.value = state.history[state.historyIdx];
      } else {
        state.historyIdx = state.history.length;
        inputEl.value = '';
      }
      autoResize(inputEl);
    }
  });

  inputEl.addEventListener('input', function () { autoResize(inputEl); });

  sendBtn.onclick = function () { sendCommand(inputEl.value); };

  clearBtn.onclick = function () {
    logEl.innerHTML = '';
    addMsg('🧹 Consola limpiada', 'info');
  };

  window.addEventListener('blur', async function () {
    if (state.cryptoKey && state.isConnected && state.ws) {
      var p = JSON.stringify({ action: 'page_blur', role: currentRole });
      state.ws.send(await encryptMessage(p, state.cryptoKey));
    }
  });

  window.addEventListener('focus', async function () {
    if (state.cryptoKey && state.isConnected && state.ws) {
      var p = JSON.stringify({ action: 'page_focus', role: currentRole });
      state.ws.send(await encryptMessage(p, state.cryptoKey));
    }
  });

  addMsg('🐝 Colmena OS <strong>Inteligente</strong> para rol <strong>' + currentRole + '</strong>', 'info');
  addMsg('💡 Prueba: <em>"lista los proyetos"</em> (con errores) - el NLU corrige automáticamente', 'info');

  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }

})();
