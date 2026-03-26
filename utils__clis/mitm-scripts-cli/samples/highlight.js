// v1 — outline semantic elements
(() => {
    const s = document.createElement('style');
    s.textContent = 'header,nav,main,article,section,aside,footer,[role="banner"],[role="navigation"],[role="main"],[role="article"],[role="contentinfo"]{outline:2px solid rgba(78,205,196,0.5)!important;outline-offset:-1px!important;position:relative!important}header::after{content:"header"}nav::after{content:"nav"}main::after{content:"main"}article::after{content:"article"}section::after{content:"section"}aside::after{content:"aside"}footer::after{content:"footer"}header::after,nav::after,main::after,article::after,section::after,aside::after,footer::after{position:absolute;top:0;left:0;z-index:99999;background:rgba(78,205,196,0.85);color:#000;font:bold 9px/1 monospace;padding:2px 4px;pointer-events:none}';
    document.head.appendChild(s);
})();
