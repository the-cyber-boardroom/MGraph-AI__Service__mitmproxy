# """Inject scripts — client-side JS payloads injected before </body>.
#
# Each script is a self-contained IIFE that runs in the browser.
# The proxy injects the script into every HTML response when mitm-mode=inject.
# """
#
# # BBC universal filter — works across bbc.co.uk/news, bbc.co.uk/sport, and article pages.
# # Uses data-testid="promo" which is BBC's shared card component across all properties.
# # Self-shielding: cards start blurred via CSS, script un-blurs after scoring.
# BBC_FILTER_SCRIPT = r"""
# (() => {
#     if (window.__bbcFilter && typeof window.__bbcFilter.destroy === 'function') {
#         window.__bbcFilter.destroy();
#     }
#
#     let CURRENT_THRESHOLD = 0;
#     const STORY_BLUR_AMOUNT = '7px';
#     const AD_BLUR_AMOUNT = '10px';
#     const QUIET_WINDOW_MS = 4000;
#     const SETTLE_RERUNS = [150, 400, 900, 1800, 3200];
#
#     // ═══════════════════════════════════════════════════════════════
#     // Word lists — tiered by strength
#     //   tier 3 = strong signal  (3 pts per hit)
#     //   tier 2 = clear signal   (2 pts per hit)
#     //   tier 1 = mild signal    (1 pt per hit)
#     // Headlines get 2x multiplier, summaries get 1x
#     // ═══════════════════════════════════════════════════════════════
#
#     const positiveT3 = [
#         'breakthrough', 'victory', 'champion', 'champions', 'rescued',
#         'reunited', 'miracle', 'historic', 'record-breaking', 'triumph',
#         'incredible', 'remarkable', 'inspirational', 'life-saving',
#         'unanimous', 'exonerated', 'acquitted', 'liberated',
#     ];
#
#     const positiveT2 = [
#         'win', 'wins', 'won', 'celebrate', 'celebrates', 'celebration',
#         'record', 'milestone', 'award', 'awarded', 'saved', 'rescuers',
#         'success', 'successful', 'recovery', 'recover', 'hope', 'hopeful',
#         'joy', 'joyful', 'progress', 'solution', 'solutions', 'resolved',
#         'improve', 'improved', 'improvement', 'restored', 'reopen',
#         'goal', 'goals', 'clean sheet', 'comeback', 'promotion', 'promoted',
#         'qualified', 'qualifies', 'medal', 'medals', 'gold medal',
#         'title', 'trophy', 'crowned', 'unbeaten',
#         'boost', 'boosted', 'surges', 'surging', 'soars', 'rises',
#         'peace', 'ceasefire', 'agreement', 'deal', 'treaty',
#         'freed', 'released', 'cleared', 'approved', 'praised',
#         'innovation', 'discovery', 'cure', 'vaccine',
#         'generous', 'donation', 'charity', 'volunteer', 'hero', 'heroes',
#         'thrilling', 'stunning', 'magnificent', 'brilliant', 'superb',
#         'delight', 'delighted', 'overjoyed', 'proud', 'pride',
#     ];
#
#     const positiveT1 = [
#         'secure', 'funding increase', 'sign up', 'learn more',
#         'delivered', 'positive', 'back in the wild',
#         'scores', 'scoring', 'through', 'qualify',
#         'top six', 'play-offs', 'playoff', 'semi-final', 'semifinal',
#         'signs', 'signed', 'extension', 'returns', 'return',
#         'fit again', 'host', 'reaches', 'reach final',
#         'growth', 'growing', 'gains', 'gaining',
#         'support', 'supporting', 'backed', 'backing',
#         'new', 'launch', 'launched', 'opens', 'opening',
#         'safe', 'safely', 'protect', 'protected',
#         'happy', 'happiness', 'smile', 'smiling', 'laugh',
#         'enjoy', 'enjoyed', 'exciting', 'excited',
#         'strong', 'stronger', 'strength', 'resilient',
#         'together', 'united', 'unity', 'community',
#         'beat', 'beats', 'advance', 'advances', 'progresses',
#     ];
#
#     const negativeT3 = [
#         'killed', 'murder', 'murdered', 'massacre', 'genocide',
#         'terrorism', 'terrorist', 'atrocity', 'catastrophic',
#         'catastrophe', 'devastating', 'devastation', 'carnage',
#         'epidemic', 'pandemic', 'famine', 'execution', 'executed',
#         'torture', 'tortured', 'rape', 'raped', 'trafficking',
#         'mass shooting', 'suicide bomb', 'war crimes',
#     ];
#
#     const negativeT2 = [
#         'war', 'strike', 'bomb', 'bombed', 'bombing', 'cluster bomb',
#         'arrested', 'spying', 'destroys', 'destroyed', 'destruction',
#         'death', 'deaths', 'dead', 'dies', 'died', 'dying',
#         'crisis', 'charged', 'jail', 'jailed', 'prison', 'sentenced',
#         'outbreak', 'humiliation', 'humiliated', 'collapse', 'collapsed',
#         'terror', 'corruption', 'fraud', 'scam', 'scandal',
#         'failure', 'failed', 'chaos',
#         'conflict', 'violence', 'violent', 'attack', 'attacked', 'assault',
#         'injury', 'injured', 'injuries', 'crash', 'crashed', 'crashes',
#         'defeat', 'shock defeat', 'relegated', 'relegation', 'sacked',
#         'banned', 'ban', 'suspended', 'suspension', 'punishment',
#         'abuse', 'abused', 'abusing', 'exploitation', 'neglect',
#         'shooting', 'stabbing', 'stabbed', 'weapon', 'weapons',
#         'explosion', 'exploded', 'inferno', 'blaze',
#         'racism', 'racist', 'discrimination', 'hate crime',
#         'victims', 'victim', 'tragedy', 'tragic',
#         'threat', 'threatens', 'threatened', 'threatening',
#         'flee', 'fleeing', 'refugees', 'displaced',
#         'poverty', 'homeless', 'starving', 'starvation',
#         'pollution', 'contaminated', 'toxic', 'disaster',
#         'recession', 'bankruptcy', 'bankrupt', 'insolvent',
#     ];
#
#     const negativeT1 = [
#         'alert', 'degraded', 'confiscated', 'inflation',
#         'falls', 'falling', 'fell', 'decline', 'declining',
#         'alleges', 'alleged', 'allegations', 'urgent',
#         'cuts', 'cut', 'falter', 'removed', 'overturned',
#         'blow', 'misses', 'miss', 'loss', 'lose', 'loses',
#         'dumped out', 'knocked out', 'eliminated',
#         'criticism', 'criticised', 'criticized',
#         'fallout', 'breaching', 'breach',
#         'wrong', 'lenient',
#         'fears', 'fear', 'worried', 'worry', 'concern', 'concerns',
#         'warns', 'warning', 'warned', 'danger', 'dangerous',
#         'risk', 'risky', 'unsafe', 'uncertain', 'uncertainty',
#         'protests', 'protest', 'protesters', 'riot', 'riots',
#         'dispute', 'disputed', 'row', 'clash', 'clashes',
#         'shortage', 'shortages', 'delays', 'delayed', 'disruption',
#         'struggle', 'struggling', 'struggles', 'suffer', 'suffering',
#         'anger', 'angry', 'furious', 'outrage', 'outraged',
#         'controversial', 'controversy', 'backlash',
#         'resign', 'resigned', 'resignation', 'fired', 'axed',
#         'reject', 'rejected', 'rejection', 'denied', 'denies',
#         'broken', 'damage', 'damaged', 'damages',
#         'worse', 'worst', 'worsening', 'deteriorating',
#         'slump', 'slumps', 'plunge', 'plunges', 'plummets',
#         'investigation', 'investigated', 'probe', 'inquiry',
#         'error', 'errors', 'mistake', 'mistakes', 'blunder',
#     ];
#
#     // ═══════════════════════════════════════════════════════════════
#     // Scoring engine
#     // ═══════════════════════════════════════════════════════════════
#
#     function escapeRegExp(v) { return v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
#
#     function countOccurrences(text, phrase) {
#         if (!text || !phrase) return 0;
#         const re = new RegExp('\\b' + escapeRegExp(phrase) + '\\b', 'gi');
#         const m = text.match(re);
#         return m ? m.length : 0;
#     }
#
#     function scoreBucket(text, words, dir, tierWeight, hitWeight, cap) {
#         let score = 0; const hits = [];
#         for (const w of words) {
#             const c = Math.min(countOccurrences(text, w), cap);
#             if (c > 0) {
#                 const delta = dir * c * tierWeight * hitWeight;
#                 score += delta;
#                 hits.push({ word: w, count: c, delta });
#             }
#         }
#         return { score, hits };
#     }
#
#     function computeScore(headline, summary) {
#         const h = (headline || '').toLowerCase();
#         const s = (summary  || '').toLowerCase();
#         const cap = 2;
#
#         const hp3 = scoreBucket(h, positiveT3, +1, 3, 2, cap);
#         const hp2 = scoreBucket(h, positiveT2, +1, 2, 2, cap);
#         const hp1 = scoreBucket(h, positiveT1, +1, 1, 2, cap);
#         const hn3 = scoreBucket(h, negativeT3, -1, 3, 2, cap);
#         const hn2 = scoreBucket(h, negativeT2, -1, 2, 2, cap);
#         const hn1 = scoreBucket(h, negativeT1, -1, 1, 2, cap);
#
#         const sp3 = scoreBucket(s, positiveT3, +1, 3, 1, cap);
#         const sp2 = scoreBucket(s, positiveT2, +1, 2, 1, cap);
#         const sp1 = scoreBucket(s, positiveT1, +1, 1, 1, cap);
#         const sn3 = scoreBucket(s, negativeT3, -1, 3, 1, cap);
#         const sn2 = scoreBucket(s, negativeT2, -1, 2, 1, cap);
#         const sn1 = scoreBucket(s, negativeT1, -1, 1, 1, cap);
#
#         const headlineScore = hp3.score + hp2.score + hp1.score + hn3.score + hn2.score + hn1.score;
#         const summaryScore  = sp3.score + sp2.score + sp1.score + sn3.score + sn2.score + sn1.score;
#
#         const allHits = [
#             ...hp3.hits, ...hp2.hits, ...hp1.hits, ...hn3.hits, ...hn2.hits, ...hn1.hits,
#             ...sp3.hits, ...sp2.hits, ...sp1.hits, ...sn3.hits, ...sn2.hits, ...sn1.hits,
#         ];
#
#         return { total: headlineScore + summaryScore, headlineScore, summaryScore, hits: allHits };
#     }
#
#     // ═══════════════════════════════════════════════════════════════
#     // UI — styles, cards, badges
#     // ═══════════════════════════════════════════════════════════════
#
#     function injectStyles() {
#         const existing = document.getElementById('bbc-filter-style');
#         if (existing) existing.remove();
#         const style = document.createElement('style');
#         style.id = 'bbc-filter-style';
#         style.textContent = `
#             div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) {
#                 filter: blur(${STORY_BLUR_AMOUNT}) saturate(0.72) !important;
#                 opacity: 0.38 !important;
#             }
#             div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) a,
#             div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) * {
#                 pointer-events: none !important; user-select: none !important;
#             }
#             .bbc-filter-processed { position: relative !important; }
#             .bbc-filter-blurred { opacity: 0.72; }
#             .bbc-filter-content-blur { filter: blur(${STORY_BLUR_AMOUNT}) saturate(0.72); }
#             .bbc-filter-clear { outline: 2px solid rgba(0,128,0,0.28); outline-offset: 2px; }
#             .bbc-filter-score-badge {
#                 position: absolute; right: 8px; bottom: 8px; z-index: 9999;
#                 font: bold 11px/1 monospace; padding: 3px 6px; border-radius: 4px;
#                 pointer-events: none; color: #fff;
#             }
#             .bbc-filter-score-pos { background: rgba(0,128,0,0.85); }
#             .bbc-filter-score-neg { background: rgba(180,0,0,0.85); }
#             .bbc-filter-score-zero { background: rgba(80,80,80,0.75); }
#             .bbc-filter-link-disabled, .bbc-filter-link-disabled * {
#                 pointer-events: none !important; cursor: default !important;
#             }
#             .bbc-filter-ad-softened {
#                 position: relative !important;
#                 filter: blur(${AD_BLUR_AMOUNT}) grayscale(0.45) brightness(0.9);
#                 opacity: 0.5; pointer-events: none !important;
#             }
#         `;
#         document.head.appendChild(style);
#     }
#
#     function getHeadline(card) {
#         return card.querySelector('h3')?.textContent?.trim() ||
#                card.querySelector('[role="heading"]')?.textContent?.trim() ||
#                card.querySelector('a')?.textContent?.trim() || '';
#     }
#
#     function getSummary(card) {
#         return [...card.querySelectorAll('p')].map(p => p.textContent.trim()).filter(Boolean).join(' ');
#     }
#
#     function getStoryCards() {
#         return [...document.querySelectorAll('div[data-testid="promo"]')]
#             .filter(c => !c.closest('header, footer, nav, [data-component="ad-slot"]'))
#             .filter(c => getHeadline(c).length > 0);
#     }
#
#     function ensureWrapper(card) {
#         let w = card.querySelector(':scope > .bbc-filter-card-content');
#         if (w) return w;
#         w = document.createElement('div'); w.className = 'bbc-filter-card-content';
#         [...card.childNodes].forEach(ch => {
#             if (ch.nodeType === 1 && ch.classList?.contains('bbc-filter-score-badge')) return;
#             w.appendChild(ch);
#         });
#         card.appendChild(w); return w;
#     }
#
#     function resetCards() {
#         getStoryCards().forEach(card => {
#             card.querySelectorAll(':scope > .bbc-filter-score-badge').forEach(b => b.remove());
#             card.classList.remove('bbc-filter-processed','bbc-filter-blurred','bbc-filter-clear','bbc-filter-link-disabled');
#             const w = card.querySelector(':scope > .bbc-filter-card-content');
#             if (w) { w.classList.remove('bbc-filter-content-blur'); [...w.childNodes].forEach(ch => card.insertBefore(ch, w)); w.remove(); }
#             card.querySelectorAll('a').forEach(a => {
#                 if (!a.getAttribute('href') && a.dataset.originalHref) a.setAttribute('href', a.dataset.originalHref);
#                 a.removeAttribute('tabindex'); a.removeAttribute('aria-disabled');
#                 a.style.pointerEvents = ''; a.style.cursor = '';
#             });
#             card.removeAttribute('data-bbc-filter-ready');
#         });
#     }
#
#     function disableLinks(card) {
#         card.classList.add('bbc-filter-link-disabled');
#         card.querySelectorAll('a[href]').forEach(a => {
#             a.dataset.originalHref = a.getAttribute('href') || '';
#             a.removeAttribute('href'); a.setAttribute('tabindex','-1'); a.setAttribute('aria-disabled','true');
#             a.style.pointerEvents = 'none'; a.style.cursor = 'default';
#         });
#     }
#
#     function getAdNodes() {
#         return [...new Set(['.dotcom-ad','[data-component="ad-slot"]','[id^="dotcom-"]'].flatMap(s => [...document.querySelectorAll(s)]))];
#     }
#
#     function processStories() {
#         const cards = getStoryCards();
#         if (!cards.length) return;
#         cards.forEach(card => {
#             card.classList.add('bbc-filter-processed');
#             const scoring = computeScore(getHeadline(card), getSummary(card));
#             const score = scoring.total;
#
#             const badge = document.createElement('div');
#             badge.className = 'bbc-filter-score-badge ' +
#                 (score > 0 ? 'bbc-filter-score-pos' : score < 0 ? 'bbc-filter-score-neg' : 'bbc-filter-score-zero');
#             badge.textContent = (score > 0 ? '+' : '') + score;
#             card.appendChild(badge);
#
#             const wrapper = ensureWrapper(card);
#             if (score < CURRENT_THRESHOLD) {
#                 card.classList.add('bbc-filter-blurred'); wrapper.classList.add('bbc-filter-content-blur'); disableLinks(card);
#             } else { card.classList.add('bbc-filter-clear'); }
#             card.setAttribute('data-bbc-filter-ready', '1');
#         });
#     }
#
#     function processAds() {
#         getAdNodes().forEach(ad => { ad.classList.add('bbc-filter-ad-softened'); ad.querySelectorAll('a,iframe').forEach(n => { n.style.pointerEvents='none'; }); });
#     }
#
#     function applyAll() { resetCards(); processStories(); processAds(); }
#
#     function debounce(fn, delay) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), delay); }; }
#
#     function startRuntime() {
#         let observer = null, quietTimer = null, destroyed = false, processing = false;
#
#         function stopAfterQuiet() {
#             clearTimeout(quietTimer);
#             quietTimer = setTimeout(() => { if (!destroyed && observer) { observer.disconnect(); observer = null; } }, QUIET_WINDOW_MS);
#         }
#
#         function connect() {
#             if (destroyed || observer) return;
#             observer = new MutationObserver(mutations => {
#                 if (destroyed || processing) return;
#                 for (const m of mutations) {
#                     if (m.type !== 'childList') continue;
#                     for (const n of [...m.addedNodes, ...m.removedNodes]) {
#                         if (!(n instanceof Element)) continue;
#                         if (n.classList?.contains('bbc-filter-score-badge') || n.classList?.contains('bbc-filter-card-content')) continue;
#                         if (n.matches?.('div[data-testid="promo"]') || n.querySelector?.('div[data-testid="promo"]') ||
#                             n.matches?.('.dotcom-ad,[data-component="ad-slot"]') || n.querySelector?.('.dotcom-ad,[data-component="ad-slot"]'))
#                         { rerun(); stopAfterQuiet(); return; }
#                     }
#                 }
#             });
#             observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
#         }
#
#         function run() {
#             if (destroyed) return;
#             processing = true; if (observer) observer.disconnect();
#             try { applyAll(); } finally { processing = false; connect(); }
#         }
#
#         const rerun = debounce(run, 120);
#         run();
#         SETTLE_RERUNS.forEach(ms => setTimeout(() => { if (!destroyed) run(); }, ms));
#         connect(); stopAfterQuiet();
#
#         return {
#             destroy() {
#                 destroyed = true; clearTimeout(quietTimer); if (observer) observer.disconnect();
#                 resetCards(); getAdNodes().forEach(a => a.classList.remove('bbc-filter-ad-softened'));
#                 const s = document.getElementById('bbc-filter-style'); if (s) s.remove();
#                 delete window.__bbcFilter;
#             },
#             applyAll: run
#         };
#     }
#
#     function debugScores() {
#         const scored = getStoryCards().map(card => {
#             const scoring = computeScore(getHeadline(card), getSummary(card));
#             return {
#                 score: scoring.total,
#                 h: scoring.headlineScore,
#                 s: scoring.summaryScore,
#                 blurred: scoring.total < CURRENT_THRESHOLD,
#                 title: getHeadline(card).slice(0, 50),
#                 hits: scoring.hits.map(h => h.word + '(' + (h.delta > 0 ? '+' : '') + h.delta + ')').join(', '),
#             };
#         });
#         console.table(scored.sort((a, b) => a.score - b.score));
#         return scored;
#     }
#
#     function boot() {
#         injectStyles();
#         const runtime = startRuntime();
#         window.__bbcFilter = runtime;
#         window.setThreshold = v => { CURRENT_THRESHOLD = Number(v); runtime.applyAll(); };
#         window.showAll      = () => { CURRENT_THRESHOLD = -Infinity; runtime.applyAll(); };
#         window.showPositive = () => { CURRENT_THRESHOLD = 1; runtime.applyAll(); };
#         window.debugScores  = debugScores;
#     }
#
#     if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
#     else boot();
# })();
# """.strip()
