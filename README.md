# MGraph AI Service — mitmproxy

[![Current Release](https://img.shields.io/badge/release-v0.8.36-blue)](https://github.com/the-cyber-boardroom/MGraph-AI__Service__mitmproxy/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-diniscruz%2Fmgraph--ai--service--mitmproxy-2496ED)](https://hub.docker.com/r/diniscruz/mgraph-ai-service-mitmproxy)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![CI Pipeline - DEV](https://github.com/the-cyber-boardroom/MGraph-AI__Service__mitmproxy/actions/workflows/ci-pipeline__dev.yml/badge.svg)](https://github.com/the-cyber-boardroom/MGraph-AI__Service__mitmproxy/actions)

An intelligent **man-in-the-middle (MITM) HTTP proxy** that rewrites the text
content of web pages as you browse — masking, hashing, sentiment-filtering, or
injecting client-side filter scripts — all controlled by cookies.

The actual [mitmproxy](https://mitmproxy.org/) process runs a thin interceptor
addon ([`_ec2_files/fastapi_interceptor.py`](_ec2_files/fastapi_interceptor.py))
that forwards every request/response to **this** FastAPI service, which makes
all the decisions. The service embeds its downstream MGraph-AI services
(cache, html, html-graph, semantic-text) **in-memory** (`run_in_memory = True`),
so the published container is fully self-contained.

> **Deeper docs:** [`docs/architecture.md`](docs/architecture.md) and the
> versioned design briefs under [`docs/dev/`](docs/dev/) — in particular the
> [technical architecture guide](docs/dev/llm-briefs/).

## 🎯 What it does

For every intercepted `text/html` response, the service runs a 3-step
transformation pipeline (HTML → hash map → transform → rebuild HTML) that
preserves page structure while changing the text. What it does is chosen by the
`mitm-mode` cookie:

| `mitm-mode` cookie | Effect | Needs |
|---|---|---|
| `off` | Pass through unchanged | — |
| `hashes` | Replace all text with hashes | — |
| `xxx` | Replace all text with `xxx` | — |
| `abcde-by-size` | Replace text with letters sized by word length | — |
| `roundtrip` | Parse → rebuild (structure validation) | — |
| `xxx-negative[-N]` | Mask only negative-sentiment text | AWS Comprehend |
| `inject` | Inject a per-domain JS filter script (from S3) | S3 bucket |

Behaviour is driven entirely by `mitm-*` cookies (not URL params). See
[`Enum__HTML__Transformation_Mode`](mgraph_ai_service_mitmproxy/schemas/html/Enum__HTML__Transformation_Mode.py)
for the full list.

## 🚀 Quick Start

There are three ways to run this locally, from easiest to most hands-on.

### Option A — Docker Compose (recommended)

Runs the **published Docker Hub image** plus a mitmproxy container wired to it.
No Python environment needed, and it's the quickest way to verify a deployed
image or to start using the proxy as another dev/agent.

```bash
git clone https://github.com/the-cyber-boardroom/MGraph-AI__Service__mitmproxy.git
cd MGraph-AI__Service__mitmproxy

docker compose up            # pulls both images and starts them
```

That's it — `docker compose up` works with no configuration. It starts:

- **HTTP/HTTPS proxy** on `localhost:8080` (auth: `mitm-user` / `mitm-pass`)
- **mitmweb UI** on http://localhost:8081
- **FastAPI service** on http://localhost:10011 (`/docs`, `/console`)
- **CA certificate** written to `./certs/mitmproxy-ca-cert.pem` (stable across restarts)

To override the image version, ports, credentials, or add S3 credentials for
`inject`/sentiment modes, copy `.env.example` to `.env` and edit it:

```bash
cp .env.example .env         # then edit, e.g. SERVICE_VERSION=v0.8.34
docker compose up
```

Pin `SERVICE_VERSION` to a specific release to test that exact deployed image.
Run `docker compose pull` to fetch newer images, and `docker compose down` to stop.

Then [point your browser at the proxy](#-using-it-from-a-browser).

### Option B — Service from source + mitmproxy in Docker

Runs the FastAPI service locally with `uvicorn` (hot-reload) and a mitmproxy
container built from the interceptor. Best when you're **changing the service
code**. Full walk-through in [`docs/dev/running-locally.md`](docs/dev/running-locally.md).

```bash
cp .local-server.env.example .local-server.env                                              # edit values
cp tests/integration/service/mitmproxy/.build.env.example tests/integration/service/mitmproxy/.build.env

./scripts/run-locally.sh              # terminal 1: FastAPI service on :10016
./scripts/run-mitmproxy-locally.sh    # terminal 2: mitmproxy container on :8080 / :8081
```

### Option C — Service only

Just the ASGI app, no proxy — useful for hitting the API directly or the web console.

```bash
pip install -e . && pip install -r requirements-test.txt
export FAST_API__AUTH__API_KEY__NAME="x-api-key"
export FAST_API__AUTH__API_KEY__VALUE="local-dev-key"
./scripts/run-locally.sh              # http://localhost:10016/docs
```

## 🌐 Using it from a browser

Once the proxy is up (Option A or B):

1. **Set the proxy** — Firefox → Settings → Network Settings → Manual proxy:
   `localhost` port `8080`, and tick *"Also use this proxy for HTTPS"*.
2. **Log in** — when prompted, use the proxy credentials
   (`mitm-user` / `mitm-pass` by default; the `PROXY_AUTH_*` values in `.env`).
3. **Install the CA** — import `certs/mitmproxy-ca-cert.pem`
   (Firefox → Settings → Certificates → Authorities → Import), or browse to
   http://mitm.it via the proxy. Only needed once — the CA is stable across restarts.
4. **Pick a mode** — set a `mitm-mode` cookie on the site you're viewing
   (e.g. `mitm-mode=hashes`). The web console at http://localhost:10011/console
   (or `:10016/console` for Option B) helps drive this.

> The interceptor only forwards `GET` + `text/html` responses to the service;
> assets and other methods pass through untouched.

## 📖 API

With the service running, the interactive docs are at `/docs` (Swagger) and
`/redoc`. Key endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/proxy/process-request` | POST | Called by the interceptor per request |
| `/proxy/process-response` | POST | Called by the interceptor per response (transform / inject) |
| `/proxy/get-proxy-stats` | GET | Proxy statistics |
| `/proxy/reset-proxy-stats` | POST | Reset statistics |
| `/cache/health`, `/cache/stats`, `/cache/config` | GET | Cache introspection |
| `/info/health`, `/info/version` | GET | Service health / version |
| `/console` | GET | Static web console (mitmproxy simulator) |

All endpoints require the API key header (`x-api-key` by default).

## ⚙️ Configuration

| Variable | Description | Required | Default |
|---|---|---|---|
| `FAST_API__AUTH__API_KEY__NAME` | Header name for the API key | Yes | — |
| `FAST_API__AUTH__API_KEY__VALUE` | API key value | Yes | — |
| `CACHE__SERVICE__BUCKET_NAME` | S3 bucket for cache + inject scripts | For `inject` | — |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` | AWS creds for S3 | For `inject` | — |
| `AUTH__SERVICE__AWS__COMPREHEND__*` | Comprehend proxy for sentiment modes | For `xxx-negative` | — |
| `AWS_REGION` | **Triggers Lambda mode** — do not set for local/Docker runs | No | — |

> ⚠️ Use `AWS_DEFAULT_REGION`, **not** `AWS_REGION`, for local/Docker runs:
> the presence of `AWS_REGION` makes `lambda_handler.py` try to load AWS Lambda
> dependency layers.

The interceptor side (inside the mitmproxy container) reads
`FASTAPI_BASE_URL`, `FASTAPI_API_KEY_NAME`, `FASTAPI_API_KEY_VALUE`.

## 🐳 Docker image

CI builds and publishes a multi-arch (amd64 + arm64) image to Docker Hub:

```bash
docker run -p 10011:10011 \
    -e FAST_API__AUTH__API_KEY__NAME=x-api-key \
    -e FAST_API__AUTH__API_KEY__VALUE=local-dev-key \
    diniscruz/mgraph-ai-service-mitmproxy:latest
```

Docker Hub push is controlled per-branch (see [CI/CD](#-cicd)) via the
`push_to_docker_hub` pipeline input.

## 🧪 Testing

```bash
pytest                                       # all tests
pytest --cov=mgraph_ai_service_mitmproxy     # with coverage
pytest tests/unit                            # unit tests (what CI runs, against LocalStack)
```

```
tests/
├── unit/           # unit tests (run in CI against LocalStack: s3, lambda, iam, logs, ec2)
├── integration/    # Docker / EC2 container creation (needs Docker/AWS)
└── deploy_aws/     # deployment tests (these actually deploy)
```

## 🚀 CI/CD

Thin per-branch workflows call the reusable
[`ci-pipeline.yml`](.github/workflows/ci-pipeline.yml): run tests → increment
git tag → (optional) deploy to AWS Lambda → (optional) build & push the Docker image.

| Branch | Tests | Docker Hub push | AWS Lambda |
|---|---|---|---|
| `dev` push | ✅ | ❌ (opt-in via manual run checkbox) | ❌ |
| `main` push | ✅ | ✅ | ✅ |
| `prod` (manual) | ✅ | ✅ | ✅ |

To publish a dev image on demand: Actions → *CI Pipeline - DEV* → *Run workflow*
→ tick *"Also push the Docker image to Docker Hub"*.

## 🔗 Related Projects

- [OSBot-Utils](https://github.com/owasp-sbot/OSBot-Utils) — type-safe core utilities
- [OSBot-Fast-API](https://github.com/owasp-sbot/OSBot-Fast-API) — FastAPI utilities
- [OSBot-AWS](https://github.com/owasp-sbot/OSBot-AWS) — AWS integration layer

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE).

---

Created and maintained by [The Cyber Boardroom](https://github.com/the-cyber-boardroom) team.
