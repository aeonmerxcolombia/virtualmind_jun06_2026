/* ============================================
   THEME MANAGER - VirtualMind Staging v3
   7 temas fijos con cobertura total
   ============================================ */

const ThemeManager = {
  VERSION: '3.0',
  STORAGE_KEY: 'vm_theme_prefs',

  palettes: {
    light: {
      label: 'Claro', icon: '☀️',
      bgBody: '#ffffff', bgCard: '#ffffff', bgSurface: '#f8fafc',
      bgSidebar: '#fafafa', bgHeader: '#ffffff', bgInput: '#ffffff',
      textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8',
      accent: '#4f46e5', accentHover: '#4338ca', accentSoft: 'rgba(79,70,229,0.08)',
      accentBorder: '#c7d2fe', border: '#e2e8f0', borderInput: '#d1d5db',
      overlay: 'rgba(255,255,255,0.95)',
    },
    dark: {
      label: 'Oscuro', icon: '🌙',
      bgBody: '#090D16', bgCard: 'rgba(15,23,42,0.65)', bgSurface: 'rgba(15,23,42,0.5)',
      bgSidebar: 'rgba(15,23,42,0.8)', bgHeader: 'rgba(15,23,42,0.8)', bgInput: 'rgba(15,23,42,0.8)',
      textPrimary: '#f1f5f9', textSecondary: '#94a3b8', textMuted: '#64748b',
      accent: '#6366f1', accentHover: '#818cf8', accentSoft: 'rgba(99,102,241,0.15)',
      accentBorder: 'rgba(99,102,241,0.3)', border: 'rgba(255,255,255,0.08)', borderInput: 'rgba(255,255,255,0.15)',
      overlay: 'rgba(0,0,0,0.8)',
    },
    ocean: {
      label: 'Océano', icon: '🌊',
      bgBody: '#eef2ff', bgCard: '#ffffff', bgSurface: '#e8edf8',
      bgSidebar: '#e2e8f5', bgHeader: '#ffffff', bgInput: '#ffffff',
      textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8',
      accent: '#0ea5e9', accentHover: '#0284c7', accentSoft: 'rgba(14,165,233,0.12)',
      accentBorder: '#bae6fd', border: '#cbd5e1', borderInput: '#94a3b8',
      overlay: 'rgba(255,255,255,0.95)',
    },
    forest: {
      label: 'Bosque', icon: '🌿',
      bgBody: '#f0fdf4', bgCard: '#ffffff', bgSurface: '#dcfce7',
      bgSidebar: '#bbf7d0', bgHeader: '#ffffff', bgInput: '#ffffff',
      textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8',
      accent: '#16a34a', accentHover: '#15803d', accentSoft: 'rgba(22,163,74,0.12)',
      accentBorder: '#bbf7d0', border: '#bbf7d0', borderInput: '#86efac',
      overlay: 'rgba(255,255,255,0.95)',
    },
    royal: {
      label: 'Real', icon: '👑',
      bgBody: '#faf5ff', bgCard: '#ffffff', bgSurface: '#f3e8ff',
      bgSidebar: '#ede9fe', bgHeader: '#ffffff', bgInput: '#ffffff',
      textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8',
      accent: '#8b5cf6', accentHover: '#7c3aed', accentSoft: 'rgba(139,92,246,0.12)',
      accentBorder: '#ddd6fe', border: '#e4d5f5', borderInput: '#c4b5fd',
      overlay: 'rgba(255,255,255,0.95)',
    },
    sunset: {
      label: 'Atardecer', icon: '🌅',
      bgBody: '#fff7ed', bgCard: '#ffffff', bgSurface: '#ffedd5',
      bgSidebar: '#fed7aa', bgHeader: '#ffffff', bgInput: '#ffffff',
      textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8',
      accent: '#f97316', accentHover: '#ea580c', accentSoft: 'rgba(249,115,22,0.12)',
      accentBorder: '#fed7aa', border: '#fed7aa', borderInput: '#fdba74',
      overlay: 'rgba(255,255,255,0.95)',
    },
    midnight: {
      label: 'Medianoche', icon: '🌃',
      bgBody: '#0f172a', bgCard: 'rgba(30,41,59,0.85)', bgSurface: 'rgba(30,41,59,0.6)',
      bgSidebar: 'rgba(15,23,42,0.9)', bgHeader: 'rgba(30,41,59,0.85)', bgInput: 'rgba(30,41,59,0.85)',
      textPrimary: '#e2e8f0', textSecondary: '#94a3b8', textMuted: '#64748b',
      accent: '#3b82f6', accentHover: '#60a5fa', accentSoft: 'rgba(59,130,246,0.15)',
      accentBorder: 'rgba(59,130,246,0.3)', border: 'rgba(255,255,255,0.08)', borderInput: 'rgba(255,255,255,0.15)',
      overlay: 'rgba(0,0,0,0.85)',
    },
  },

  defaults: {
    theme: 'light',
    accent: '#4f46e5',
    bgBody: '#ffffff',
    textPrimary: '#0f172a',
    cardBg: '#ffffff',
    btnRadius: '0.75rem',
    fontSize: '100',
  },

  prefs: null,

  palettesList() {
    return ['light', 'dark', 'ocean', 'forest', 'royal', 'sunset', 'midnight'];
  },

  init() {
    this.loadLocal();
    this.loadFromServer();
  },

  loadLocal() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (raw) {
        this.prefs = { ...this.defaults, ...JSON.parse(raw) };
      } else {
        this.prefs = { ...this.defaults };
      }
    } catch {
      this.prefs = { ...this.defaults };
    }
  },

  loadFromServer() {
    const token = localStorage.getItem('token') || localStorage.getItem('bearer_token');
    if (!token) {
      this.apply();
      this.injectUI();
      return;
    }
    const apiBase = window.location.pathname.startsWith('/staging/') ? '/staging-api' : '';
    fetch(`${apiBase}/users/theme-preferences`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        if (data && data.theme_preferences && typeof data.theme_preferences === 'object') {
          this.prefs = { ...this.defaults, ...data.theme_preferences };
          this.saveLocal();
        }
      })
      .catch(() => {})
      .finally(() => {
        this.apply();
        this.injectUI();
      });
  },

  save() {
    this.saveLocal();
    this.syncToServer();
  },

  saveLocal() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.prefs));
    } catch {}
  },

  getPalette(themeName) {
    return this.palettes[themeName] || this.palettes.light;
  },

  generateThemeCSS(pal) {
    const T = (v, fallback) => v || fallback;
    const b = pal;
    return `
/* ===== BODY & HEADINGS ===== */
body { background-color: ${T(b.bgBody,'#fff')} !important; color: ${T(b.textPrimary,'#0f172a')} !important; }
h1, h2, h3, h4, h5, h6 { color: ${T(b.textPrimary,'#0f172a')} !important; }
.gradient-bg { background: ${T(b.bgBody,'#fff')} !important; }

/* ===== CARDS ===== */
.card-glass, [class*="card-glass"] { background: ${T(b.bgCard,'#fff')} !important; border: 1px solid ${T(b.border,'#e2e8f0')} !important; }

/* ===== GRAYSCALE BACKGROUNDS: SLATE ===== */
.bg-slate-50, .bg-slate-100, .bg-slate-200, .bg-slate-300, .bg-slate-400,
.bg-slate-500, .bg-slate-600, .bg-slate-700, .bg-slate-800, .bg-slate-900,
.bg-slate-950 { background: ${T(b.bgBody,'#fff')} !important; }
[class*="bg-slate-50/"], [class*="bg-slate-100/"], [class*="bg-slate-200/"],
[class*="bg-slate-300/"], [class*="bg-slate-400/"], [class*="bg-slate-500/"],
[class*="bg-slate-600/"], [class*="bg-slate-700/"], [class*="bg-slate-800/"],
[class*="bg-slate-900/"], [class*="bg-slate-950/"] { background: ${T(b.bgBody,'#fff')} !important; }

/* ===== GRAYSCALE BACKGROUNDS: GRAY ===== */
.bg-gray-50, .bg-gray-100, .bg-gray-200, .bg-gray-300, .bg-gray-400,
.bg-gray-500, .bg-gray-600, .bg-gray-700, .bg-gray-800, .bg-gray-900,
.bg-gray-950 { background: ${T(b.bgSurface,'#f1f5f9')} !important; }
[class*="bg-gray-50/"], [class*="bg-gray-100/"], [class*="bg-gray-200/"],
[class*="bg-gray-300/"], [class*="bg-gray-400/"], [class*="bg-gray-500/"],
[class*="bg-gray-600/"], [class*="bg-gray-700/"], [class*="bg-gray-800/"],
[class*="bg-gray-900/"], [class*="bg-gray-950/"] { background: ${T(b.bgSurface,'#f1f5f9')} !important; }

/* ===== WHITE BG + OPACITIES ===== */
.bg-white, .bg-white\\/5, .bg-white\\/10, .bg-white\\/20, .bg-white\\/30,
.bg-white\\/40, .bg-white\\/50, .bg-white\\/60, .bg-white\\/70, .bg-white\\/80,
.bg-white\\/90, .bg-white\\/95 { background: ${T(b.bgCard,'#fff')} !important; }

/* ===== HEX / DARK BACKGROUNDS (overrides slate/gray) ===== */
.bg-\\[#090D16\\], .bg-\\[#090d16\\], .bg-\\[#0a0e1a\\], .bg-\\[#0f172a\\],
.bg-\\[#23262f\\], .bg-\\[#1e293b\\] { background: ${T(b.bgBody,'#fff')} !important; }
[class*="bg-\\[#"] { background: ${T(b.bgBody,'#fff')} !important; }

/* ===== ACCENT BACKGROUNDS (indigo) ===== */
.bg-indigo-50, .bg-indigo-100 { background: ${T(b.accentSoft,'#eef2ff')} !important; }
.bg-indigo-200 { background: ${T(b.accentSoft,'#dbeafe')} !important; }
.bg-indigo-500 { background: ${T(b.accent,'#6366f1')} !important; }
.bg-indigo-600 { background: ${T(b.accent,'#4f46e5')} !important; }
.bg-indigo-700 { background: ${T(b.accentHover,'#3730a3')} !important; }
.bg-indigo-500\\/10, .bg-indigo-600\\/10 { background: ${T(b.accentSoft,'rgba(79,70,229,0.08)')} !important; }
.bg-indigo-600\\/20 { background: ${T(b.accentSoft,'rgba(79,70,229,0.12)')} !important; }
.bg-indigo-600\\/30 { background: ${T(b.accentSoft,'rgba(79,70,229,0.18)')} !important; }

/* ===== GRAYSCALE TEXT: SLATE ===== */
.text-slate-50, .text-slate-100, .text-slate-200 { color: ${T(b.textPrimary,'#0f172a')} !important; }
.text-slate-300 { color: ${T(b.textPrimary,'#1e293b')} !important; }
.text-slate-400 { color: ${T(b.textSecondary,'#475569')} !important; }
.text-slate-500 { color: ${T(b.textSecondary,'#475569')} !important; }
.text-slate-600 { color: ${T(b.textMuted,'#64748b')} !important; }
.text-slate-700, .text-slate-800, .text-slate-900 { color: ${T(b.textPrimary,'#0f172a')} !important; }
[class*="text-slate-50/"], [class*="text-slate-100/"], [class*="text-slate-200/"],
[class*="text-slate-300/"], [class*="text-slate-400/"], [class*="text-slate-500/"],
[class*="text-slate-600/"], [class*="text-slate-700/"], [class*="text-slate-800/"],
[class*="text-slate-900/"], [class*="text-slate-950/"] { color: ${T(b.textPrimary,'#0f172a')} !important; }

/* ===== GRAYSCALE TEXT: GRAY ===== */
.text-gray-50, .text-gray-100, .text-gray-200, .text-gray-300 { color: ${T(b.textPrimary,'#0f172a')} !important; }
.text-gray-400 { color: ${T(b.textSecondary,'#475569')} !important; }
.text-gray-500 { color: ${T(b.textSecondary,'#475569')} !important; }
.text-gray-600 { color: ${T(b.textMuted,'#64748b')} !important; }
.text-gray-700 { color: ${T(b.textSecondary,'#475569')} !important; }
.text-gray-800, .text-gray-900 { color: ${T(b.textPrimary,'#0f172a')} !important; }
[class*="text-gray-50/"], [class*="text-gray-100/"], [class*="text-gray-200/"],
[class*="text-gray-300/"], [class*="text-gray-400/"], [class*="text-gray-500/"],
[class*="text-gray-600/"], [class*="text-gray-700/"], [class*="text-gray-800/"],
[class*="text-gray-900/"], [class*="text-gray-950/"] { color: ${T(b.textPrimary,'#0f172a')} !important; }

/* ===== WHITE TEXT ===== */
.text-white { color: ${T(b.textPrimary,'#0f172a')} !important; }
.text-white\\/5, .text-white\\/10, .text-white\\/20, .text-white\\/30,
.text-white\\/40, .text-white\\/50, .text-white\\/60, .text-white\\/70,
.text-white\\/75, .text-white\\/80, .text-white\\/85, .text-white\\/90,
.text-white\\/95 { color: ${T(b.textPrimary,'#0f172a')} !important; }
[class*="text-white/"] { color: ${T(b.textMuted,'#64748b')} !important; }

/* ===== ACCENT TEXT (indigo) ===== */
.text-indigo-50, .text-indigo-100, .text-indigo-200, .text-indigo-400 { color: ${T(b.accent,'#4f46e5')} !important; }
.text-indigo-300 { color: ${T(b.accentHover,'#6366f1')} !important; }
.text-indigo-500 { color: ${T(b.accent,'#6366f1')} !important; }
.text-indigo-600, .text-indigo-700, .text-indigo-800 { color: ${T(b.accentHover,'#3730a3')} !important; }
[class*="text-indigo-50/"], [class*="text-indigo-100/"], [class*="text-indigo-200/"],
[class*="text-indigo-300/"], [class*="text-indigo-400/"], [class*="text-indigo-500/"],
[class*="text-indigo-600/"], [class*="text-indigo-700/"], [class*="text-indigo-800/"],
[class*="text-indigo-900/"] { color: ${T(b.accent,'#4f46e5')} !important; }

/* ===== BORDERS: SLATE ===== */
.border-slate-100, .border-slate-200, .border-slate-300, .border-slate-400,
.border-slate-500, .border-slate-600, .border-slate-700, .border-slate-800,
.border-slate-900, .border-slate-950 { border-color: ${T(b.border,'#e2e8f0')} !important; }
[class*="border-slate-50/"], [class*="border-slate-100/"], [class*="border-slate-200/"],
[class*="border-slate-300/"], [class*="border-slate-400/"], [class*="border-slate-500/"],
[class*="border-slate-600/"], [class*="border-slate-700/"], [class*="border-slate-800/"],
[class*="border-slate-900/"] { border-color: ${T(b.border,'#e2e8f0')} !important; }

/* ===== BORDERS: GRAY ===== */
.border-gray-100, .border-gray-200, .border-gray-300, .border-gray-400,
.border-gray-500, .border-gray-600, .border-gray-700, .border-gray-800,
.border-gray-900, .border-gray-950 { border-color: ${T(b.border,'#e2e8f0')} !important; }
[class*="border-gray-50/"], [class*="border-gray-100/"], [class*="border-gray-200/"],
[class*="border-gray-300/"], [class*="border-gray-400/"], [class*="border-gray-500/"],
[class*="border-gray-600/"], [class*="border-gray-700/"], [class*="border-gray-800/"],
[class*="border-gray-900/"] { border-color: ${T(b.border,'#e2e8f0')} !important; }

/* ===== BORDERS: WHITE OPACITY ===== */
.border-white\\/5, .border-white\\/10, .border-white\\/20, .border-white\\/30,
.border-white\\/40, .border-white\\/50 { border-color: ${T(b.border,'#e2e8f0')} !important; }
[class*="border-white/"] { border-color: ${T(b.border,'#e2e8f0')} !important; }

/* ===== BORDERS: INDIGO / ACCENT ===== */
.border-indigo-100, .border-indigo-200 { border-color: ${T(b.accentBorder,'#c7d2fe')} !important; }
.border-indigo-300, .border-indigo-400, .border-indigo-500, .border-indigo-600,
.border-indigo-700 { border-color: ${T(b.accentBorder,'#c7d2fe')} !important; }
[class*="border-indigo-50/"], [class*="border-indigo-100/"], [class*="border-indigo-200/"],
[class*="border-indigo-300/"], [class*="border-indigo-400/"], [class*="border-indigo-500/"],
[class*="border-indigo-600/"] { border-color: ${T(b.accentBorder,'#c7d2fe')} !important; }

/* ===== SIDEBAR & HEADER ===== */
aside, [class*="sidebar"], .sidebar { background: ${T(b.bgSidebar,'#fafafa')} !important; border-right: 1px solid ${T(b.border,'#e2e8f0')} !important; }
header { background: ${T(b.bgHeader,'#fff')} !important; border-bottom: 1px solid ${T(b.border,'#e2e8f0')} !important; }

/* ===== TABLES ===== */
table, thead, tbody, tr, th, td { background: transparent !important; }
thead tr, thead th, th { background: ${T(b.bgSurface,'#f8fafc')} !important; color: ${T(b.textSecondary,'#475569')} !important; }
td { color: ${T(b.textPrimary,'#0f172a')} !important; border-color: ${T(b.border,'#e2e8f0')} !important; }
tr:hover td, tr:hover th { background: ${T(b.bgSurface,'#f1f5f9')} !important; }

/* ===== MODALS & OVERLAYS ===== */
[class*="modal"], [class*="overlay"] { background: ${T(b.overlay,'rgba(255,255,255,0.95)')} !important; }
[class*="modal"] > div, [class*="modal-content"] { background: ${T(b.bgCard,'#fff')} !important; }

/* ===== INPUTS ===== */
select, input, textarea { background: ${T(b.bgInput,'#fff')} !important; border-color: ${T(b.borderInput,'#d1d5db')} !important; color: ${T(b.textPrimary,'#0f172a')} !important; }
select:focus, input:focus, textarea:focus { border-color: ${T(b.accent,'#4f46e5')} !important; outline: none !important; box-shadow: 0 0 0 2px ${T(b.accentSoft,'rgba(79,70,229,0.15)')} !important; }

/* ===== DROPDOWNS & POPOVERS ===== */
[class*="dropdown"], [class*="popover"] { background: ${T(b.bgCard,'#fff')} !important; border: 1px solid ${T(b.border,'#e2e8f0')} !important; }

/* ===== HOVER: BACKGROUNDS ===== */
.hover\\:bg-gray-50:hover, .hover\\:bg-gray-100:hover, .hover\\:bg-gray-200:hover,
.hover\\:bg-gray-300:hover { background: ${T(b.bgSurface,'#f1f5f9')} !important; }
.hover\\:bg-gray-600:hover, .hover\\:bg-gray-700:hover,
.hover\\:bg-gray-800:hover { background: ${T(b.bgSurface,'#e2e8f0')} !important; }
.hover\\:bg-slate-100:hover, .hover\\:bg-slate-200:hover { background: ${T(b.bgSurface,'#f1f5f9')} !important; }
.hover\\:bg-slate-600:hover, .hover\\:bg-slate-700:hover,
.hover\\:bg-slate-800:hover, .hover\\:bg-slate-800\\/80:hover,
.hover\\:bg-slate-900:hover { background: ${T(b.bgSurface,'#e2e8f0')} !important; }
.hover\\:bg-indigo-50:hover, .hover\\:bg-indigo-100:hover,
.hover\\:bg-indigo-200:hover { background: ${T(b.accentSoft,'rgba(79,70,229,0.08)')} !important; }
.hover\\:bg-indigo-500:hover, .hover\\:bg-indigo-600:hover { background: ${T(b.accent,'#4f46e5')} !important; }
.hover\\:bg-indigo-600\\/20:hover { background: ${T(b.accentSoft,'rgba(79,70,229,0.15)')} !important; }
.hover\\:bg-indigo-700:hover { background: ${T(b.accentHover,'#4338ca')} !important; }

/* ===== HOVER: TEXT ===== */
.hover\\:text-gray-600:hover, .hover\\:text-gray-700:hover,
.hover\\:text-gray-800:hover, .hover\\:text-gray-900:hover { color: ${T(b.textPrimary,'#0f172a')} !important; }
.hover\\:text-indigo-300:hover { color: ${T(b.accentHover,'#6366f1')} !important; }
.hover\\:text-indigo-500:hover, .hover\\:text-indigo-600:hover,
.hover\\:text-indigo-700:hover, .hover\\:text-indigo-800:hover { color: ${T(b.accent,'#4f46e5')} !important; }
.hover\\:text-white:hover { color: #fff !important; }

/* ===== MISC ===== */
.backdrop-blur-md, .backdrop-blur-lg { background: ${T(b.bgCard,'#fff')} !important; }
.menu-item { color: ${T(b.textSecondary,'#475569')} !important; }
.menu-item:hover { background: ${T(b.bgSurface,'#f1f5f9')} !important; color: ${T(b.textPrimary,'#0f172a')} !important; }
kbd { background: ${T(b.bgSurface,'#f1f5f9')} !important; border-color: ${T(b.border,'#e2e8f0')} !important; color: ${T(b.textMuted,'#64748b')} !important; }
#notifDropdown { background: ${T(b.bgCard,'#fff')} !important; border: 1px solid ${T(b.border,'#e2e8f0')} !important; }
.chat-bubble.bg-white, .chat-bubble.bg-gray-50 { background: ${T(b.bgCard,'#fff')} !important; border: 1px solid ${T(b.border,'#e2e8f0')} !important; }
.chat-bubble.bg-indigo-600 { background: ${T(b.accent,'#4f46e5')} !important; }
.chat-bubble.bg-indigo-50 { background: ${T(b.bgSurface,'#f8fafc')} !important; border: 1px solid ${T(b.border,'#e2e8f0')} !important; }
.glow-blob { opacity: 0.15 !important; }
`;
  },

  injectThemeCSS(themeName) {
    const old = document.getElementById('vmThemeStyle');
    if (old) old.remove();
    const pal = this.getPalette(themeName);
    const style = document.createElement('style');
    style.id = 'vmThemeStyle';
    style.textContent = this.generateThemeCSS(pal);
    document.head.appendChild(style);
  },

  apply() {
    const p = this.prefs;
    const theme = p.theme || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    this.injectThemeCSS(theme);

    const scale = parseInt(p.fontSize) / 100;
    document.documentElement.style.fontSize = (16 * scale) + 'px';
    document.documentElement.style.setProperty('--btn-radius', p.btnRadius);
  },

  setTheme(theme) {
    this.prefs.theme = theme;
    if (theme === 'light') {
      this.resetToDefaults();
    } else if (theme === 'dark') {
      this.prefs.accent = '#6366f1';
    } else if (this.palettes[theme]) {
      const pal = this.palettes[theme];
      this.prefs.accent = pal.accent;
      this.prefs.bgBody = pal.bgBody;
      this.prefs.textPrimary = pal.textPrimary;
      this.prefs.cardBg = pal.bgCard;
    }
    this.apply();
    this.save();
    this.updateUI();
  },

  resetToDefaults() {
    Object.assign(this.prefs, this.defaults);
  },

  lighten(hex, percent) {
    if (!hex || hex[0] !== '#') return hex;
    const num = parseInt(hex.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.min(255, (num >> 16) + amt);
    const G = Math.min(255, ((num >> 8) & 0x00FF) + amt);
    const B = Math.min(255, (num & 0x0000FF) + amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
  },

  syncToServer() {
    const token = localStorage.getItem('token') || localStorage.getItem('bearer_token');
    if (!token) return;
    const apiBase = window.location.pathname.startsWith('/staging/') ? '/staging-api' : '';
    fetch(`${apiBase}/users/theme-preferences`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ theme_preferences: this.prefs }),
    }).catch(() => {});
  },

  /* ========== UI ========== */

  injectUI() {
    const header = document.querySelector('header');
    if (!header) return;
    const btn = document.createElement('button');
    btn.id = 'themeToggleBtn';
    btn.title = 'Personalizar tema visual';
    btn.className = 'relative bg-white hover:bg-gray-100 text-gray-600 hover:text-gray-900 p-2.5 rounded-xl border border-gray-200 transition-all';
    btn.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path></svg>';
    btn.onclick = () => this.openPanel();
    const headerActions = header.querySelector('.flex.items-center.space-x-3, .flex.items-center.gap-3, .flex');
    if (headerActions) headerActions.appendChild(btn);
    else header.appendChild(btn);
    this.injectPanel();
  },

  injectPanel() {
    const panel = document.createElement('div');
    panel.id = 'themePanel';
    panel.style.cssText = 'display:none;position:fixed;top:0;right:0;width:380px;height:100vh;background:#fff;z-index:9999;box-shadow:-4px 0 30px rgba(0,0,0,0.15);overflow-y:auto;transition:transform 0.3s ease;transform:translateX(100%);border-left:1px solid #e2e8f0;';
    panel.innerHTML = this.buildPanelHTML();
    document.body.appendChild(panel);

    const overlay = document.createElement('div');
    overlay.id = 'themeOverlay';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:9998;';
    overlay.onclick = () => this.closePanel();
    document.body.appendChild(overlay);
  },

  buildPanelHTML() {
    const p = this.prefs;
    const currentTheme = p.theme;

    const presetBtns = this.palettesList().map(key => {
      const pal = this.palettes[key];
      const active = currentTheme === key;
      return `<button data-theme="${key}" onclick="ThemeManager.setTheme('${key}')" style="flex:0 0 calc(33.33% - 0.35rem);padding:0.6rem 0.4rem;border-radius:0.75rem;border:2px solid ${active ? '#4f46e5' : '#e2e8f0'};background:${pal.bgBody};color:${pal.textPrimary};font-weight:${active ? '700' : '500'};font-size:0.7rem;cursor:pointer;transition:all 0.2s;text-align:center;min-height:52px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;">${pal.icon}<span>${pal.label}</span></button>`;
    }).join('');

    return `
      <div style="padding:1.5rem;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;">
        <h2 style="font-size:1.1rem;font-weight:700;color:#0f172a;">🎨 Temas Visuales</h2>
        <button onclick="ThemeManager.closePanel()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:#64748b;">&times;</button>
      </div>
      <div style="padding:1.5rem;display:flex;flex-direction:column;gap:1.5rem;">
        <div>
          <label style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:0.75rem;display:block;">Elige un tema</label>
          <div style="display:flex;flex-wrap:wrap;gap:0.5rem;">
            ${presetBtns}
          </div>
        </div>

        <div>
          <label style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:0.5rem;display:block;">Tamaño de Fuente</label>
          <div style="display:flex;gap:0.75rem;align-items:center;">
            <span style="font-size:0.75rem;color:#64748b;">A</span>
            <input type="range" min="75" max="150" value="${p.fontSize}" oninput="ThemeManager.setFontSize(this.value)" style="flex:1;accent-color:#4f46e5;">
            <span style="font-size:1.25rem;color:#64748b;">A</span>
            <span style="font-size:0.8rem;font-weight:600;min-width:2.5rem;text-align:center;color:#0f172a;">${p.fontSize}%</span>
          </div>
        </div>

        <div>
          <label style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:0.5rem;display:block;">Redondeo de Botones</label>
          <div style="display:flex;gap:0.5rem;">
            <button onclick="ThemeManager.setBtnRadius('0.375rem')" style="flex:1;padding:0.5rem;border-radius:0.25rem;border:2px solid ${p.btnRadius === '0.375rem' ? '#4f46e5' : '#e2e8f0'};font-size:0.7rem;font-weight:500;cursor:pointer;background:#fff;color:#0f172a;">Recto</button>
            <button onclick="ThemeManager.setBtnRadius('0.75rem')" style="flex:1;padding:0.5rem;border-radius:0.5rem;border:2px solid ${p.btnRadius === '0.75rem' ? '#4f46e5' : '#e2e8f0'};font-size:0.7rem;font-weight:500;cursor:pointer;background:#fff;color:#0f172a;">Normal</button>
            <button onclick="ThemeManager.setBtnRadius('1.25rem')" style="flex:1;padding:0.5rem;border-radius:1rem;border:2px solid ${p.btnRadius === '1.25rem' ? '#4f46e5' : '#e2e8f0'};font-size:0.7rem;font-weight:500;cursor:pointer;background:#fff;color:#0f172a;">Redondo</button>
          </div>
        </div>

        <button onclick="ThemeManager.resetToDefaults();ThemeManager.setTheme('light');ThemeManager.closePanel();" style="padding:0.75rem;border-radius:0.75rem;border:1px solid #e2e8f0;background:#f8fafc;color:#64748b;font-size:0.85rem;font-weight:500;cursor:pointer;">Restablecer valores predeterminados</button>
        <div style="font-size:0.7rem;color:#94a3b8;text-align:center;">Los cambios se guardan automáticamente</div>
      </div>
    `;
  },

  openPanel() {
    const panel = document.getElementById('themePanel');
    const overlay = document.getElementById('themeOverlay');
    if (panel) { panel.style.display = 'block'; setTimeout(() => panel.style.transform = 'translateX(0)', 10); }
    if (overlay) overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';
  },

  closePanel() {
    const panel = document.getElementById('themePanel');
    const overlay = document.getElementById('themeOverlay');
    if (panel) { panel.style.transform = 'translateX(100%)'; setTimeout(() => panel.style.display = 'none', 300); }
    if (overlay) overlay.style.display = 'none';
    document.body.style.overflow = '';
  },

  updateUI() {
    const panel = document.getElementById('themePanel');
    if (panel) panel.innerHTML = this.buildPanelHTML();
  },

  setFontSize(val) {
    this.prefs.fontSize = val;
    const scale = parseInt(val) / 100;
    document.documentElement.style.fontSize = (16 * scale) + 'px';
    this.save();
    this.updateUI();
  },

  setBtnRadius(val) {
    this.prefs.btnRadius = val;
    document.documentElement.style.setProperty('--btn-radius', val);
    this.save();
    this.updateUI();
  },
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
} else {
  ThemeManager.init();
}
