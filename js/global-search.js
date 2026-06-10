(function() {
  if (window.__globalSearchLoaded) return;
  window.__globalSearchLoaded = true;

  const API_BASE = 'https://gestordecursos.pegui.edu.co:8000';

  function getToken() {
    return localStorage.getItem('token');
  }

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  // --- Create search modal ---
  function createSearchModal() {
    if (document.getElementById('global-search-modal')) return;

    const overlay = document.createElement('div');
    overlay.id = 'global-search-overlay';
    overlay.style.cssText = `
      position: fixed; inset: 0; z-index: 99999;
      background: rgba(0,0,0,0.6);
      backdrop-filter: blur(4px);
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding-top: 10vh;
    `;

    const modal = document.createElement('div');
    modal.id = 'global-search-modal';
    modal.style.cssText = `
      width: 640px; max-width: 94vw;
      background: #0f172a;
      border: 1px solid rgba(99,102,241,0.3);
      border-radius: 16px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.8);
      overflow: hidden;
      animation: gsFadeIn 0.2s ease-out;
    `;

    modal.innerHTML = `
      <style>
        @keyframes gsFadeIn { from { opacity:0; transform:translateY(-12px) scale(0.97); } to { opacity:1; transform:translateY(0) scale(1); } }
        .gs-input { width:100%; padding:18px 20px; background:#02040a; border:none; color:#e2e8f0; font-size:15px; outline:none; font-family:'Inter',sans-serif; }
        .gs-input::placeholder { color:#475569; }
        .gs-results { max-height:420px; overflow-y:auto; padding:8px; }
        .gs-group-label { padding:8px 14px 4px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:#6366f1; opacity:0.6; }
        .gs-item { display:flex; align-items:center; gap:12px; padding:10px 14px; border-radius:10px; cursor:pointer; transition:all 0.15s; text-decoration:none; color:#cbd5e1; }
        .gs-item:hover { background:rgba(99,102,241,0.12); color:#fff; }
        .gs-item-icon { font-size:18px; flex-shrink:0; width:28px; text-align:center; }
        .gs-item-content { flex:1; min-width:0; }
        .gs-item-title { font-size:13px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .gs-item-subtitle { font-size:11px; color:#64748b; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .gs-item-type { font-size:9px; padding:2px 8px; border-radius:999px; background:rgba(99,102,241,0.15); color:#818cf8; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; flex-shrink:0; }
        .gs-empty { text-align:center; padding:40px 20px; color:#475569; font-size:13px; }
        .gs-shortcut { font-size:10px; color:#334155; padding:18px 20px 12px; border-top:1px solid rgba(255,255,255,0.04); text-align:center; font-family:'Inter',sans-serif; }
        .gs-shortcut kbd { display:inline-block; padding:1px 6px; border-radius:4px; background:#1e293b; color:#94a3b8; font-size:10px; border:1px solid #334155; margin:0 2px; font-family:monospace; }
        .gs-spinner { text-align:center; padding:30px; }
        .gs-spinner::after { content:''; display:inline-block; width:22px; height:22px; border:2px solid #334155; border-top-color:#6366f1; border-radius:50%; animation:gsSpin 0.6s linear infinite; }
        @keyframes gsSpin { to { transform:rotate(360deg); } }
        .gs-highlight { background:rgba(99,102,241,0.2); border-radius:2px; padding:0 2px; }
        .gs-results::-webkit-scrollbar { width:4px; }
        .gs-results::-webkit-scrollbar-track { background:transparent; }
        .gs-results::-webkit-scrollbar-thumb { background:#334155; border-radius:999px; }
      </style>
      <input type="text" class="gs-input" placeholder="Buscar proyectos, usuarios, tareas, documentos, RRHH... (Ctrl+K)" autofocus id="gs-input">
      <div class="gs-results" id="gs-results">
        <div class="gs-empty">Escribe para buscar en todo VirtualMind</div>
      </div>
      <div class="gs-shortcut">
        <kbd>↑</kbd> <kbd>↓</kbd> navegar · <kbd>Enter</kbd> abrir · <kbd>Esc</kbd> cerrar
      </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    const input = modal.querySelector('#gs-input');
    const resultsContainer = modal.querySelector('#gs-results');

    let selectedIndex = -1;
    let currentResults = [];
    let currentRequestId = 0;

    function closeSearch() {
      overlay.style.display = 'none';
      overlay.querySelector('#gs-input').blur();
      selectedIndex = -1;
      currentResults = [];
    }

    function openSearch() {
      overlay.style.display = 'flex';
      const inp = overlay.querySelector('#gs-input');
      inp.value = '';
      inp.focus();
      resultsContainer.innerHTML = '<div class="gs-empty">Escribe para buscar en todo VirtualMind</div>';
      selectedIndex = -1;
      currentResults = [];
    }

    function navigateResults(direction) {
      const items = resultsContainer.querySelectorAll('.gs-item');
      if (!items.length) return;
      items.forEach(i => i.style.background = '');
      selectedIndex = Math.max(0, Math.min(selectedIndex + direction, items.length - 1));
      items[selectedIndex].style.background = 'rgba(99,102,241,0.2)';
      items[selectedIndex].scrollIntoView({ block: 'nearest' });
    }

    function openSelected() {
      const items = resultsContainer.querySelectorAll('.gs-item');
      if (selectedIndex >= 0 && selectedIndex < items.length) {
        const link = items[selectedIndex].getAttribute('data-url');
        if (link) {
          closeSearch();
          const iframe = document.getElementById('mainFrame');
          if (iframe) {
            iframe.src = link;
          } else {
            window.location.href = link;
          }
        }
      }
    }

    function highlightText(text, query) {
      if (!query) return escapeHtml(text);
      const escaped = escapeHtml(text);
      const words = query.trim().split(/\s+/).filter(w => w.length > 0);
      let result = escaped;
      for (const word of words) {
        const re = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        result = result.replace(re, '<span class="gs-highlight">$1</span>');
      }
      return result;
    }

    const performSearch = debounce(async function(query) {
      if (!query.trim()) {
        resultsContainer.innerHTML = '<div class="gs-empty">Escribe para buscar en todo VirtualMind</div>';
        currentResults = [];
        selectedIndex = -1;
        return;
      }

      const reqId = ++currentRequestId;
      resultsContainer.innerHTML = '<div class="gs-spinner"></div>';
      selectedIndex = -1;

      try {
        const token = getToken();
        const res = await fetch(`${API_BASE}/search/?q=${encodeURIComponent(query.trim())}&limit=6`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!res.ok) throw new Error('Search failed');
        if (reqId !== currentRequestId) return;

        const data = await res.json();
        currentResults = data.results || [];

        if (!currentResults.length) {
          resultsContainer.innerHTML = '<div class="gs-empty">Sin resultados para <strong>' + escapeHtml(query) + '</strong></div>';
          return;
        }

        // Group by type
        const groups = {};
        const labels = { proyecto: 'Proyectos', usuario: 'Usuarios', tarea: 'Tareas', documento: 'Documentos', rrhh: 'RRHH' };
        const icons = { proyecto: '📁', usuario: '👤', tarea: '✅', documento: '📄', rrhh: '👔' };

        for (const r of currentResults) {
          if (!groups[r.type]) groups[r.type] = [];
          groups[r.type].push(r);
        }

        let html = '';
        for (const [type, items] of Object.entries(groups)) {
          html += `<div class="gs-group-label">${labels[type] || type}</div>`;
          for (const item of items) {
            html += `<a class="gs-item" data-url="${escapeHtml(item.url || '#')}" href="${escapeHtml(item.url || '#')}" onclick="event.preventDefault(); window.__gsOpen ? window.__gsOpen('${escapeHtml(item.url || '#')}') : (function(){document.getElementById('global-search-overlay').style.display='none';var f=document.getElementById('mainFrame');if(f)f.src='${escapeHtml(item.url || '#')}';})();">
              <span class="gs-item-icon">${item.icon || '📄'}</span>
              <div class="gs-item-content">
                <div class="gs-item-title">${highlightText(item.title, query)}</div>
                <div class="gs-item-subtitle">${highlightText(item.subtitle || '', query)}</div>
              </div>
              <span class="gs-item-type">${(labels[type] || type).slice(0, -1) || type}</span>
            </a>`;
          }
        }
        resultsContainer.innerHTML = html;

      } catch (err) {
        if (reqId === currentRequestId) {
          resultsContainer.innerHTML = '<div class="gs-empty">Error al buscar. Intenta de nuevo.</div>';
        }
      }
    }, 250);

    input.addEventListener('input', function() {
      performSearch(this.value);
    });

    input.addEventListener('keydown', function(e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); navigateResults(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); navigateResults(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); openSelected(); }
      else if (e.key === 'Escape') { closeSearch(); }
    });

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closeSearch();
    });

    // Global keyboard shortcut
    document.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (overlay.style.display === 'flex') {
          closeSearch();
        } else {
          openSearch();
        }
      }
    });

    window.__gsOpen = function(url) {
      closeSearch();
      const iframe = document.getElementById('mainFrame');
      if (iframe) iframe.src = url;
    };
  }

  // Initialize on DOMContentLoaded or immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createSearchModal);
  } else {
    createSearchModal();
  }
})();
