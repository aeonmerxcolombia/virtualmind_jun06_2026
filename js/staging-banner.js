(function(){
  if (!window.location.pathname.startsWith('/staging/')) return;
  if (!document.body) {
    document.addEventListener('DOMContentLoaded', arguments.callee);
    return;
  }
  var style = document.createElement('style');
  style.textContent = '.staging-banner{position:fixed;top:0;left:0;right:0;z-index:99999;background:#d97706;color:#fff;text-align:center;font-size:10px;padding:2px 0;font-family:sans-serif;letter-spacing:0.5px;font-weight:600}';
  document.head.appendChild(style);
  var b = document.createElement('div');
  b.className = 'staging-banner';
  b.textContent = '🔶 AMBIENTE DE PRUEBAS';
  document.body.prepend(b);
  document.body.style.paddingTop = '16px';
})();
