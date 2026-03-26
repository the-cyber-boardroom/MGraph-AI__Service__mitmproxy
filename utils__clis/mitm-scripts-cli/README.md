# mitm-scripts

CLI tool for managing inject scripts in S3 for the MITM proxy.

Push and pull filter scripts that the proxy injects into web pages
when `mitm-mode=inject` is set.

## Architecture

```
  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────┐
  │  mitm-scripts    │         │  S3 / Cache      │         │  mitmproxy   │
  │  CLI             │  push   │  Service         │  reads  │              │
  │                  │ ──────▶ │                   │ ◀────── │  injects     │
  │  pull/push/list  │ ◀────── │  inject/data/     │         │  <script>    │
  │                  │  pull   │  sites/{domain}/  │         │  before      │
  │                  │         │  filter.js/data   │         │  </body>     │
  └──────────────────┘         └──────────────────┘         └──────────────┘
                                                                   │
                                                                   ▼
                                                            ┌──────────────┐
                                                            │  Browser     │
                                                            │  runs the    │
                                                            │  injected    │
                                                            │  script      │
                                                            └──────────────┘
```

## How It Works

```
  S3 structure (single cache entry, cache_key='inject'):

  {namespace}/inject/data/
    └── sites/
        ├── bbc.co.uk/
        │   └── filter.js/
        │       └── data          ← the BBC filter script
        ├── theguardian.com/
        │   └── filter.js/
        │       └── data          ← empty stub (not yet populated)
        └── nytimes.com/
            └── filter.js/
                └── data          ← empty stub

  Local directory (after pull):

  sites/
    ├── bbc.co.uk/
    │   └── filter.js             ← edit this, then push
    ├── theguardian.com/
    │   └── filter.js             ← edit this, then push
    └── nytimes.com/
        └── filter.js

  samples/
    ├── banner.js                 ← push with: mitm-scripts push <domain> -s banner
    ├── border.js
    ├── stats.js
    ├── highlight.js
    └── combined.js
```

## Quick Start

```bash
# 1. Clone the repo
git clone <this-repo>
cd mitm-scripts

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install
pip install -e .

# 4. Configure — copy and edit .env
cp .env.example .env
# Edit .env with your Cache Service credentials

# 5. Check connection
mitm-scripts status

# 6. List domains with scripts
mitm-scripts list

# 7. Pull all scripts to local sites/ directory
mitm-scripts pull

# 8. Edit a script
$EDITOR sites/bbc.co.uk/filter.js

# 9. Push it back
mitm-scripts push bbc.co.uk

# 10. Push a sample script to test a domain
mitm-scripts push theguardian.com --sample combined
```

## Commands

### `mitm-scripts status`

Check connection, show cache_id and namespace.

```
  ✓ Connected to: https://cache.example.com
  ✓ Namespace:    my-namespace
  ✓ Cache ID:     abc-123-def
  ✓ Health:       OK
```

### `mitm-scripts list`

List all domains that have scripts in S3.

```
  Inject scripts (3 domains):

    bbc.co.uk
    bbc.com
    theguardian.com
```

### `mitm-scripts pull [domain]`

Pull scripts from S3 to local `sites/` directory.

```bash
mitm-scripts pull              # pull all domains
mitm-scripts pull bbc.co.uk    # pull just BBC
```

### `mitm-scripts push [domain] [--sample name]`

Push scripts from local `sites/` directory to S3.

```bash
mitm-scripts push              # push all domains in sites/
mitm-scripts push bbc.co.uk    # push just BBC
mitm-scripts push bbc.co.uk --sample combined   # push a sample script
mitm-scripts push bbc.co.uk -s banner           # shorthand
```

## Samples

Pre-built test scripts that work on any site:

| Sample | What it does |
|--------|-------------|
| `banner.js` | Purple gradient bar at top: "MITM INJECT ACTIVE" |
| `border.js` | Red dashed border around page + badge |
| `stats.js` | Floating panel with page metrics (scripts, images, links) |
| `highlight.js` | Outlines semantic elements (header, nav, main, article) |
| `combined.js` | Banner + border + mini stats — full confidence check |

Each script has a `// v1` comment at the top. Increment when editing to
confirm the proxy picks up your change.

## Workflow

```
  Developer edits filter.js locally
       │
       ▼
  mitm-scripts push bbc.co.uk        ← pushes to S3
       │
       ▼
  Proxy loads script on next request  ← no deploy, no restart
       │
       ▼
  Browser shows updated filter        ← refresh to see changes
```

## Version Convention

Add a version comment to the top of your scripts:

```javascript
// v3 — added sport-specific words, fixed false positive on 'return'
(() => {
    ...
})();
```

Increment the version when you push. You'll see it in the browser's
DevTools (Elements tab → search for `mitm-inject`) to confirm the
proxy has the latest.
