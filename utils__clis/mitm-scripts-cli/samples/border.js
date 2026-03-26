// v1 — red dashed border + badge
(() => {
    const s = document.createElement('style');
    s.textContent = 'html{border:4px dashed rgba(255,0,0,0.6)!important;box-sizing:border-box!important}body::after{content:"⚡ INJECTED — "+attr(data-mitm-host);position:fixed;bottom:8px;right:8px;z-index:999999;background:rgba(255,0,0,0.85);color:#fff;font:bold 11px/1 monospace;padding:4px 8px;border-radius:4px;pointer-events:none}';
    document.body.setAttribute('data-mitm-host', location.hostname);
    document.head.appendChild(s);
})();
