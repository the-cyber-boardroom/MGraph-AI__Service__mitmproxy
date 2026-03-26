(() => {
    const overlay = document.createElement('div');
    overlay.id = 'mitm-inject-watermark';
    overlay.style.cssText = `
        position: fixed; inset: 0; z-index: 999998;
        pointer-events: none; overflow: hidden;
        opacity: 0.06;
    `;
    const text = 'MITM INJECT ';
    const line = text.repeat(20);
    let html = '';
    for (let i = 0; i < 30; i++) {
        html += `<div style="
            white-space: nowrap;
            font: bold 24px/2.5 monospace;
            color: #000;
            transform: rotate(-35deg);
            transform-origin: 0 0;
            margin-left: ${(i % 2) * 80}px;
        ">${line}</div>`;
    }
    overlay.innerHTML = html;
    document.body.appendChild(overlay);
})();