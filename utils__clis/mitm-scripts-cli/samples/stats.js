// v1 — floating stats panel
(() => {
    const p = document.createElement('div');
    const sc = document.querySelectorAll('script').length;
    const st = document.querySelectorAll('link[rel="stylesheet"],style').length;
    const im = document.querySelectorAll('img').length;
    const lk = document.querySelectorAll('a[href]').length;
    const da = new Set(); document.querySelectorAll('*').forEach(e => { for (const a of e.attributes) if (a.name.startsWith('data-')) da.add(a.name); });
    p.style.cssText = 'position:fixed;top:12px;right:12px;z-index:999999;background:rgba(0,0,0,0.88);color:#4ecdc4;font:12px/1.6 monospace;padding:12px 16px;border-radius:8px;border:1px solid rgba(78,205,196,0.3);box-shadow:0 4px 24px rgba(0,0,0,0.4);min-width:220px;backdrop-filter:blur(8px)';
    p.innerHTML = '<div style="font-weight:bold;color:#fff;margin-bottom:6px;font-size:13px">🔬 '+location.hostname+' <span onclick="this.closest(\'div\').parentElement.remove()" style="float:right;cursor:pointer;opacity:0.5">✕</span></div><div>scripts: <b style="color:#fff">'+sc+'</b></div><div>styles: <b style="color:#fff">'+st+'</b></div><div>images: <b style="color:#fff">'+im+'</b></div><div>links: <b style="color:#fff">'+lk+'</b></div><div>data-*: <b style="color:#fff">'+da.size+' unique</b></div><div style="margin-top:6px;opacity:0.4;font-size:10px">'+new Date().toISOString().slice(0,19)+'</div>';
    document.body.appendChild(p);
})();
