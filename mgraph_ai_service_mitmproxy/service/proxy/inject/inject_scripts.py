"""Inject scripts — client-side JS payloads injected before </body>.

Each script is a self-contained IIFE that runs in the browser.
The proxy injects the script into every HTML response when mitm-mode=inject.
"""

# BBC universal filter — works across bbc.co.uk/news, bbc.co.uk/sport, and article pages.
# Uses data-testid="promo" which is BBC's shared card component across all properties.
# Self-shielding: cards start blurred via CSS, script un-blurs after scoring.
BBC_FILTER_SCRIPT = r"""
(() => {
    if (window.__bbcFilter && typeof window.__bbcFilter.destroy === 'function') {
        window.__bbcFilter.destroy();
    }

    let CURRENT_THRESHOLD = 0;
    const STORY_BLUR_AMOUNT = '7px';
    const AD_BLUR_AMOUNT = '10px';
    const QUIET_WINDOW_MS = 4000;
    const SETTLE_RERUNS = [150, 400, 900, 1800, 3200];

    const positiveWords = [
        'win', 'wins', 'won', 'victory', 'celebrate', 'celebrates',
        'breakthrough', 'record', 'milestone', 'funding increase',
        'reopen', 'restored', 'secure', 'improve', 'improved',
        'triumph', 'award', 'awarded', 'saved', 'rescuers',
        'reunited', 'back in the wild', 'sign up', 'learn more',
        'living bridge', 'delivered', 'hope', 'incredible',
        'success', 'successful', 'recovery', 'recover', 'rescued',
        'joy', 'positive', 'progress', 'solution', 'solutions',
        'goal', 'goals', 'scores', 'scoring', 'clean sheet',
        'comeback', 'through', 'qualified', 'qualifies', 'qualify',
        'title', 'champion', 'champions', 'promotion',
        'top six', 'play-offs', 'playoff', 'medal', 'medals',
        'signs', 'signed', 'extension', 'returns', 'return',
        'fit again', 'cleared', 'boost', 'boosted', 'host',
        'reaches', 'reach final', 'semi-final', 'semifinal'
    ];

    const negativeWords = [
        'war', 'killed', 'strike', 'bomb', 'cluster bomb',
        'arrested', 'murder', 'rape', 'spying', 'destroys',
        'death', 'crisis', 'charged', 'jail', 'alert',
        'outbreak', 'humiliation', 'collapse', 'catastrophic',
        'degraded', 'confiscated', 'terror', 'inflation fears',
        'devastation', 'public health', 'falls', 'crashes',
        'deepfakes', 'alleges', 'corruption', 'urgent',
        'cuts', 'catastrophic cuts', 'failure', 'failed',
        'falter', 'removed', 'overturned', 'chaos', 'conflict',
        'out', 'defeat', 'shock defeat', 'blow', 'injury', 'injured',
        'misses', 'miss', 'banned', 'ban', 'sacked', 'sack',
        'loss', 'lose', 'loses', 'dumped out', 'knocked out',
        'eliminated', 'relegated', 'relegation', 'charges',
        'charge', 'punishment', 'criticism', 'fallout', 'breaching',
        'ridiculous', 'wrong', 'what just happened', 'lenient',
        'collapse', 'humiliation'
    ];

    function escapeRegExp(v) { return v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

    function countOccurrences(text, phrase) {
        if (!text || !phrase) return 0;
        const m = text.match(new RegExp(escapeRegExp(phrase), 'gi'));
        return m ? m.length : 0;
    }

    function scoreBucket(text, words, dir, weight, cap) {
        let score = 0; const hits = [];
        for (const w of words) {
            const c = Math.min(countOccurrences(text, w), cap);
            if (c > 0) { score += dir * c * weight; hits.push({ word: w, count: c, delta: dir * c * weight }); }
        }
        return { score, hits };
    }

    function computeScore(headline, summary) {
        const h = (headline || '').toLowerCase(), s = (summary || '').toLowerCase();
        const hp = scoreBucket(h, positiveWords, +1, 2, 2), hn = scoreBucket(h, negativeWords, -1, 2, 2);
        const sp = scoreBucket(s, positiveWords, +1, 1, 2), sn = scoreBucket(s, negativeWords, -1, 1, 2);
        return { total: hp.score + hn.score + sp.score + sn.score,
                 headlineScore: hp.score + hn.score, summaryScore: sp.score + sn.score,
                 hits: { headlinePositive: hp.hits, headlineNegative: hn.hits, summaryPositive: sp.hits, summaryNegative: sn.hits } };
    }

    function injectStyles() {
        const existing = document.getElementById('bbc-filter-style');
        if (existing) existing.remove();
        const style = document.createElement('style');
        style.id = 'bbc-filter-style';
        style.textContent = `
            div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) {
                filter: blur(${STORY_BLUR_AMOUNT}) saturate(0.72) !important;
                opacity: 0.38 !important;
            }
            div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) a,
            div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) * {
                pointer-events: none !important; user-select: none !important;
            }
            .bbc-filter-processed { position: relative !important; }
            .bbc-filter-blurred { opacity: 0.72; }
            .bbc-filter-content-blur { filter: blur(${STORY_BLUR_AMOUNT}) saturate(0.72); }
            .bbc-filter-clear { outline: 2px solid rgba(0, 128, 0, 0.28); outline-offset: 2px; }
            .bbc-filter-score-badge {
                position: absolute; right: 8px; bottom: 8px; z-index: 9999;
                font: 12px/1 sans-serif; background: rgba(0,0,0,0.82); color: #fff;
                padding: 4px 6px; border-radius: 4px; pointer-events: none;
            }
            .bbc-filter-link-disabled, .bbc-filter-link-disabled * {
                pointer-events: none !important; cursor: default !important;
            }
            .bbc-filter-ad-softened {
                position: relative !important;
                filter: blur(${AD_BLUR_AMOUNT}) grayscale(0.45) brightness(0.9);
                opacity: 0.5; pointer-events: none !important;
            }
        `;
        document.head.appendChild(style);
    }

    function getHeadline(card) {
        return card.querySelector('h3')?.textContent?.trim() ||
               card.querySelector('[role="heading"]')?.textContent?.trim() ||
               card.querySelector('a')?.textContent?.trim() || '';
    }

    function getSummary(card) {
        return [...card.querySelectorAll('p')].map(p => p.textContent.trim()).filter(Boolean).join(' ');
    }

    function getStoryCards() {
        return [...document.querySelectorAll('div[data-testid="promo"]')]
            .filter(c => !c.closest('header, footer, nav, [data-component="ad-slot"]'))
            .filter(c => getHeadline(c).length > 0);
    }

    function ensureWrapper(card) {
        let w = card.querySelector(':scope > .bbc-filter-card-content');
        if (w) return w;
        w = document.createElement('div'); w.className = 'bbc-filter-card-content';
        [...card.childNodes].forEach(ch => {
            if (ch.nodeType === 1 && ch.classList?.contains('bbc-filter-score-badge')) return;
            w.appendChild(ch);
        });
        card.appendChild(w); return w;
    }

    function resetCards() {
        getStoryCards().forEach(card => {
            card.querySelectorAll(':scope > .bbc-filter-score-badge').forEach(b => b.remove());
            card.classList.remove('bbc-filter-processed','bbc-filter-blurred','bbc-filter-clear','bbc-filter-link-disabled');
            const w = card.querySelector(':scope > .bbc-filter-card-content');
            if (w) { w.classList.remove('bbc-filter-content-blur'); [...w.childNodes].forEach(ch => card.insertBefore(ch, w)); w.remove(); }
            card.querySelectorAll('a').forEach(a => {
                if (!a.getAttribute('href') && a.dataset.originalHref) a.setAttribute('href', a.dataset.originalHref);
                a.removeAttribute('tabindex'); a.removeAttribute('aria-disabled');
                a.style.pointerEvents = ''; a.style.cursor = '';
            });
            card.removeAttribute('data-bbc-filter-ready');
        });
    }

    function disableLinks(card) {
        card.classList.add('bbc-filter-link-disabled');
        card.querySelectorAll('a[href]').forEach(a => {
            a.dataset.originalHref = a.getAttribute('href') || '';
            a.removeAttribute('href'); a.setAttribute('tabindex','-1'); a.setAttribute('aria-disabled','true');
            a.style.pointerEvents = 'none'; a.style.cursor = 'default';
        });
    }

    function getAdNodes() {
        return [...new Set(['.dotcom-ad','[data-component="ad-slot"]','[id^="dotcom-"]'].flatMap(s => [...document.querySelectorAll(s)]))];
    }

    function processStories() {
        const cards = getStoryCards();
        if (!cards.length) return;
        cards.forEach(card => {
            card.classList.add('bbc-filter-processed');
            const scoring = computeScore(getHeadline(card), getSummary(card));
            const badge = document.createElement('div'); badge.className = 'bbc-filter-score-badge';
            badge.textContent = 'score: ' + scoring.total; card.appendChild(badge);
            const wrapper = ensureWrapper(card);
            if (scoring.total < CURRENT_THRESHOLD) {
                card.classList.add('bbc-filter-blurred'); wrapper.classList.add('bbc-filter-content-blur'); disableLinks(card);
            } else { card.classList.add('bbc-filter-clear'); }
            card.setAttribute('data-bbc-filter-ready', '1');
        });
    }

    function processAds() {
        getAdNodes().forEach(ad => { ad.classList.add('bbc-filter-ad-softened'); ad.querySelectorAll('a,iframe').forEach(n => { n.style.pointerEvents='none'; }); });
    }

    function applyAll() { resetCards(); processStories(); processAds(); }

    function debounce(fn, delay) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), delay); }; }

    function startRuntime() {
        let observer = null, quietTimer = null, destroyed = false, processing = false;

        function stopAfterQuiet() {
            clearTimeout(quietTimer);
            quietTimer = setTimeout(() => { if (!destroyed && observer) { observer.disconnect(); observer = null; } }, QUIET_WINDOW_MS);
        }

        function connect() {
            if (destroyed || observer) return;
            observer = new MutationObserver(mutations => {
                if (destroyed || processing) return;
                for (const m of mutations) {
                    if (m.type !== 'childList') continue;
                    for (const n of [...m.addedNodes, ...m.removedNodes]) {
                        if (!(n instanceof Element)) continue;
                        if (n.classList?.contains('bbc-filter-score-badge') || n.classList?.contains('bbc-filter-card-content')) continue;
                        if (n.matches?.('div[data-testid="promo"]') || n.querySelector?.('div[data-testid="promo"]') ||
                            n.matches?.('.dotcom-ad,[data-component="ad-slot"]') || n.querySelector?.('.dotcom-ad,[data-component="ad-slot"]'))
                        { rerun(); stopAfterQuiet(); return; }
                    }
                }
            });
            observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
        }

        function run() {
            if (destroyed) return;
            processing = true; if (observer) observer.disconnect();
            try { applyAll(); } finally { processing = false; connect(); }
        }

        const rerun = debounce(run, 120);
        run();
        SETTLE_RERUNS.forEach(ms => setTimeout(() => { if (!destroyed) run(); }, ms));
        connect(); stopAfterQuiet();

        return {
            destroy() {
                destroyed = true; clearTimeout(quietTimer); if (observer) observer.disconnect();
                resetCards(); getAdNodes().forEach(a => a.classList.remove('bbc-filter-ad-softened'));
                const s = document.getElementById('bbc-filter-style'); if (s) s.remove();
                delete window.__bbcFilter;
            },
            applyAll: run
        };
    }

    function boot() {
        injectStyles();
        const runtime = startRuntime();
        window.__bbcFilter = runtime;
        window.setThreshold = v => { CURRENT_THRESHOLD = Number(v); runtime.applyAll(); };
        window.showAll = () => { CURRENT_THRESHOLD = -Infinity; runtime.applyAll(); };
        window.showOnlyPositive = () => { CURRENT_THRESHOLD = 1; runtime.applyAll(); };
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
    else boot();
})();
""".strip()
