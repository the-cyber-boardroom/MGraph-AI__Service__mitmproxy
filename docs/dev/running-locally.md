# Running the proxy locally

Three execution modes, from easiest to most hands-on. All three end up with the
same thing: a mitmproxy listening on `localhost:8080` that forwards traffic to
the FastAPI service, plus a stable CA in `./certs/`.

| Mode | Service | Proxy | Use when |
|---|---|---|---|
| **A. Docker Compose** | published image | official image + mounted interceptor | verifying a deployed image; quick start |
| **B. Source + Docker** | `uvicorn` (hot-reload) | custom-built image | changing service code |
| **C. Service only** | `uvicorn` | — | hitting the API / console directly |

The three modes share the gitignored **`certs/`** folder as mitmproxy's confdir,
so the CA is generated once and reused across all of them — you only import it
into your browser one time.

---

## Option A — Docker Compose (published images)

Runs the exact image CI publishes to Docker Hub, wired to a mitmproxy container
over a private compose network. Nothing to build, no Python needed.

```bash
docker compose up            # pulls both images, starts them, works with zero config
```

Endpoints:

- HTTP/HTTPS proxy: `localhost:8080` (auth `mitm-user` / `mitm-pass`)
- mitmweb UI: http://localhost:8081
- FastAPI service: http://localhost:10011 (`/docs`, `/console`)
- CA cert: `./certs/mitmproxy-ca-cert.pem`

### Configuration

Everything has a default (see `docker-compose.yml`). To override, copy the
template and edit:

```bash
cp .env.example .env
```

Common overrides:

```env
SERVICE_VERSION=v0.8.34        # pin to a released image to test that exact deploy
PROXY_AUTH_USER=my-user
PROXY_AUTH_PASS=my-pass

# S3-backed inject mode (mitm-mode=inject) — loads sites/{domain}/filter.js from S3
CACHE__SERVICE__BUCKET_NAME=my-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=eu-west-1   # NEVER AWS_REGION — that switches the service into Lambda mode
```

### Lifecycle

```bash
docker compose pull          # fetch newer images
docker compose up -d         # run detached
docker compose logs -f       # follow logs
docker compose down          # stop and remove
```

### How the wiring works

- The interceptor reaches the service at `http://mitm-service:10011` — the
  compose service name resolves over the internal network, so no
  `host.docker.internal` is needed.
- `mitm-proxy` waits for `mitm-service` to pass its healthcheck (`/info/health`)
  before starting, via `depends_on: condition: service_healthy`.
- `FASTAPI_API_KEY_NAME` / `FASTAPI_API_KEY_VALUE` on the proxy must match
  `FAST_API__AUTH__API_KEY__NAME` / `__VALUE` on the service — the compose file
  keeps them in sync from the same `.env` variables.

---

## Option B — Service from source + mitmproxy in Docker

Best when you're editing the service and want `uvicorn --reload`.

```bash
cp .local-server.env.example .local-server.env                                              # edit values
cp tests/integration/service/mitmproxy/.build.env.example tests/integration/service/mitmproxy/.build.env

./scripts/run-locally.sh              # terminal 1: FastAPI service on :10016
./scripts/run-mitmproxy-locally.sh    # terminal 2: builds + starts the mitmproxy container
```

`run-mitmproxy-locally.sh` builds a custom image bundling the interceptor and
mounts `./certs/` as the confdir. It validates `.build.env` up front and prints
Firefox setup steps. Tear the container down with:

```bash
./scripts/run-mitmproxy-locally.sh cleanup
```

`.build.env` values are baked into the image at build time, so after changing
them run `cleanup` and start again to rebuild.

The interceptor reaches the service at `http://host.docker.internal:10016` on
macOS/Windows; on Linux use the docker bridge IP (`http://172.17.0.1:10016`) or
your LAN IP in `.build.env`.

---

## Option C — Service only

```bash
pip install -e . && pip install -r requirements-test.txt
export FAST_API__AUTH__API_KEY__NAME="x-api-key"
export FAST_API__AUTH__API_KEY__VALUE="local-dev-key"
./scripts/run-locally.sh              # http://localhost:10016/docs
```

No proxy — you call `/proxy/process-request` and `/proxy/process-response`
directly, or use the web console at http://localhost:10016/console.

---

## Pointing a browser at the proxy (Options A & B)

1. **Proxy** — Firefox → Settings → Network Settings → Manual proxy config:
   HTTP proxy `localhost`, port `8080`, tick *Also use this proxy for HTTPS*.
2. **Auth** — enter the `PROXY_AUTH_USER` / `PROXY_AUTH_PASS` credentials when prompted.
3. **CA** — Firefox → Settings → Privacy & Security → Certificates → View
   Certificates → Authorities → Import → select `certs/mitmproxy-ca-cert.pem`,
   trust it for websites. (Or browse to http://mitm.it through the proxy.)
4. **Mode** — set a `mitm-mode` cookie on the target site, e.g. `mitm-mode=hashes`.
   The web console helps set these.

> Firefox is convenient here because it has its own proxy setting and CA store,
> independent of the OS — so you can proxy Firefox while leaving the rest of the
> machine alone.

---

## Troubleshooting

- **`407 Proxy Authentication Required`** — the browser (or a test) isn't sending
  the proxy credentials. Check `PROXY_AUTH_USER` / `PROXY_AUTH_PASS`.
- **TLS / certificate warnings** — the CA in `certs/` isn't imported/trusted yet,
  or you're on a fresh `certs/` folder. Re-import `certs/mitmproxy-ca-cert.pem`.
- **Pages aren't transformed** — only `GET` + `text/html` responses are forwarded
  to the service; also confirm the `mitm-mode` cookie is set for that site.
- **Service tries to load Lambda layers / behaves oddly** — `AWS_REGION` is set in
  the environment. Use `AWS_DEFAULT_REGION` instead for local/Docker runs.
- **`inject` mode does nothing** — it needs S3 credentials + `CACHE__SERVICE__BUCKET_NAME`;
  the script is loaded from `sites/{domain}/filter.js` under the cache namespace.
