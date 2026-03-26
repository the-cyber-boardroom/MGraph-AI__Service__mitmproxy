// v1 — banner + border + mini stats
(() => {
    const bar = document.createElement('div');
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:999999;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font:bold 12px/1 system-ui;padding:6px 16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;gap:10px';
    bar.innerHTML = '<span>🔬 INJECT ACTIVE</span><span style="opacity:0.5">|</span><span style="font-weight:400">'+location.hostname+'</span><button onclick="this.parentElement.remove();document.body.style.marginTop=\'0\'" style="margin-left:auto;background:rgba(255,255,255,0.2);border:none;color:#fff;padding:2px 8px;border-radius:3px;cursor:pointer;font-size:11px">✕</button>';
    document.body.prepend(bar);
    document.body.style.marginTop = '32px';
    const s = document.createElement('style');
    s.textContent = 'html{border:3px solid rgba(102,126,234,0.5)!important}';
    document.head.appendChild(s);
    const sc = document.querySelectorAll('script').length;
    const im = document.querySelectorAll('img').length;
    const lk = document.querySelectorAll('a[href]').length;
    const p = document.createElement('div');
    p.style.cssText = 'position:fixed;bottom:12px;right:12px;z-index:999999;background:rgba(0,0,0,0.85);color:#4ecdc4;font:11px/1.5 monospace;padding:8px 12px;border-radius:6px;border:1px solid rgba(78,205,196,0.3);pointer-events:none';
    p.textContent = 'scripts:'+sc+' imgs:'+im+' links:'+lk;
    document.body.appendChild(p);
})();
