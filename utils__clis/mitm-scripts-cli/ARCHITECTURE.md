# Architecture: MITM Proxy Script Injection

## End-to-End Flow

```
  1. Developer writes filter.js locally
           │
           ▼
  2. mitm-scripts push bbc.co.uk
           │
           ▼
  3. Script stored in S3
     Path: {namespace}/inject/data/sites/bbc.co.uk/filter.js/data
           │
           ▼
  4. User browses www.bbc.co.uk through mitmproxy
     Cookie: mitm-mode=inject
           │
           ▼
  5. Proxy intercepts HTML response from BBC origin
           │
           ▼
  6. Proxy__Inject__Service:
     a) Extract domain: www.bbc.co.uk → bbc.co.uk
     b) Build data_key: sites/bbc.co.uk/filter.js
     c) Load script from S3 via cache_id + data_key
     d) Extract CSP nonce from HTML: <script nonce="7viV1sk5k...">
     e) Inject: <script id="mitm-inject" nonce="7viV1sk5k...">SCRIPT</script>
     f) Insert before </body>
     g) Strip Content-Security-Policy headers
           │
           ▼
  7. Modified HTML sent to browser
           │
           ▼
  8. Browser executes injected script
     - Script scores all story cards (data-testid="promo")
     - Blurs negative stories, highlights positive ones
     - MutationObserver handles lazy-loaded content
```

## Components

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │  mitm-scripts CLI                 S3 / Cache Service                │
  │  (this repo)                      (shared storage)                  │
  │                                                                     │
  │  ┌──────────────────┐            ┌──────────────────┐              │
  │  │ sites/            │   push    │ inject/data/      │              │
  │  │   bbc.co.uk/      │ ───────▶  │   sites/          │              │
  │  │     filter.js     │            │     bbc.co.uk/    │              │
  │  │   nytimes.com/    │   pull    │       filter.js   │              │
  │  │     filter.js     │ ◀───────  │     nytimes.com/  │              │
  │  └──────────────────┘            │       filter.js   │              │
  │                                   └────────┬─────────┘              │
  │  ┌──────────────────┐                      │                        │
  │  │ samples/          │                      │ reads                  │
  │  │   banner.js       │                      │                        │
  │  │   border.js       │                      ▼                        │
  │  │   stats.js        │            ┌──────────────────┐              │
  │  │   highlight.js    │            │ mitmproxy         │              │
  │  │   combined.js     │            │                   │              │
  │  └──────────────────┘            │ Proxy__Inject__   │              │
  │                                   │ Service           │              │
  │                                   │                   │              │
  │                                   │ if mitm-mode=     │              │
  │                                   │   inject:         │              │
  │                                   │   load script     │              │
  │                                   │   inject before   │              │
  │                                   │   </body>         │              │
  │                                   └────────┬─────────┘              │
  │                                            │                        │
  │                                            ▼                        │
  │                                   ┌──────────────────┐              │
  │                                   │ Browser           │              │
  │                                   │ runs script       │              │
  │                                   │ client-side       │              │
  │                                   └──────────────────┘              │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
```

## S3 Structure

One cache entry (`cache_key='inject'`) holds all scripts as data keys:

```
  cache_key: "inject"  →  cache_id (one, shared)

  data operations:
    data_key: "sites/bbc.co.uk/filter.js"       data_file_id: "data"
    data_key: "sites/bbc.com/filter.js"          data_file_id: "data"
    data_key: "sites/nytimes.com/filter.js"      data_file_id: "data"
```

## Script Lifecycle

```
  1. NEW DOMAIN
     User visits nytimes.com with inject mode
     → Proxy creates empty stub in S3
     → Nothing injected (stub = comments only)

  2. DEVELOPMENT
     Developer: mitm-scripts push nytimes.com --sample combined
     → Sample test script pushed to S3
     → Next page load shows banner/border/stats
     → Confirms injection pipeline works for this domain

  3. CUSTOM FILTER
     Developer: mitm-scripts pull nytimes.com
     → Edits sites/nytimes.com/filter.js locally
     → Writes scoring logic, card selectors, blur/reveal behavior
     → mitm-scripts push nytimes.com
     → Browser shows custom filter on next refresh

  4. ITERATION
     Developer changes filter.js, bumps version comment
     → mitm-scripts push nytimes.com
     → Refresh browser, check version in DevTools (search: mitm-inject)
     → Repeat until filter works correctly

  5. PRODUCTION
     Script is stable → team decides if they want to re-enable
     in-memory caching in the proxy for performance
```

## CSP (Content Security Policy) Handling

Many sites (including BBC) use nonce-based CSP that blocks inline scripts.
The proxy handles this:

```
  1. Extract nonce from existing <script nonce="abc123"> in the HTML
  2. Add same nonce to our injected script: <script nonce="abc123" id="mitm-inject">
  3. Strip CSP headers from response (belt and suspenders)
```

## Self-Shielding (BBC Filter Example)

The BBC filter uses CSS to blur cards before the script runs:

```css
  div[data-testid="promo"]:not([data-bbc-filter-ready="1"]) {
      filter: blur(7px);
      opacity: 0.38;
  }
```

Cards start blurred. The script processes each card, scores it, then
sets `data-bbc-filter-ready="1"`. Processed cards become visible.
No separate shield injection needed — the script is self-contained.
