# CLAUDE.md

Guidance for Claude Code (and other agents/devs) working in this repository.

## What this is

An intelligent MITM HTTP proxy. A [mitmproxy](https://mitmproxy.org/) process
runs a thin interceptor addon (`_ec2_files/fastapi_interceptor.py`) that forwards
every request/response to **this FastAPI service**, which makes all decisions
(HTML transformation, script injection, blocking, caching). The service embeds
its downstream MGraph-AI services (cache, html, html-graph, semantic-text)
**in-memory** (`run_in_memory = True`), so the published container is
self-contained.

Behaviour is driven by `mitm-*` **cookies** (not URL params). The main one is
`mitm-mode` — see `mgraph_ai_service_mitmproxy/schemas/html/Enum__HTML__Transformation_Mode.py`.

Start with `docs/architecture.md` and the briefs under `docs/dev/`. The README
is accurate; older `docs/CHANGELOG.md` is a stub.

## Running locally

Three modes, fully documented in **`docs/dev/running-locally.md`**:

- **A. `docker compose up`** — published Docker Hub image + mitmproxy container.
  Zero-config; best for verifying a deployed image or a quick start.
- **B. `./scripts/run-locally.sh` + `./scripts/run-mitmproxy-locally.sh`** —
  service from source (uvicorn --reload) + custom mitmproxy container. Best when
  changing service code.
- **C. `./scripts/run-locally.sh`** — service only.

## Testing

```bash
pytest tests/unit                            # what CI runs (against LocalStack)
pytest --cov=mgraph_ai_service_mitmproxy
```

- CI runs `tests/unit` against LocalStack (`s3,lambda,iam,logs,ec2`). Some tests
  need that S3/network and will fail in a bare local env — before claiming a
  regression, diff the failure set with and without your change (`git stash`).
- `tests/integration/` needs Docker/AWS; `tests/deploy_aws/` actually deploys.
- The repo targets **Python 3.12**. Do not develop/run on 3.14 — see the gotcha
  below.

## Conventions (OSBot Type_Safe)

- Almost every class extends `Type_Safe` (from `osbot_utils`); one class per file.
- Naming: `Domain__Subdomain__Thing` (double underscore), files match class names.
- Type-safe fields are class annotations with defaults; construction is
  keyword-only. Enums subclass `(str, Enum)` and Type_Safe coerces strings to
  them on assignment.
- Logging is `print(...)` with emojis; keep that style in the proxy path.

## Branch & CI

- Reusable pipeline: `.github/workflows/ci-pipeline.yml`; per-branch callers
  `ci-pipeline__{dev,main,prod}.yml`.
- Docker Hub push is gated by the `push_to_docker_hub` input: `main` always
  pushes; `dev` is opt-in via a manual-run checkbox; `prod` pushes.
- AWS Lambda deploy is gated by `deploy_to_aws` (disabled on dev).
- Version bumps are tag-driven in CI.

## Gotchas (learned the hard way)

- **`AWS_REGION` triggers Lambda mode.** `lambda_handler.py` treats a set
  `AWS_REGION` as "running in Lambda" and tries to load dependency layers. For
  local/Docker runs use **`AWS_DEFAULT_REGION`** instead.
- **Persistent CA lives in `certs/`** (gitignored — contains the CA private key).
  All local modes mount it as mitmproxy's confdir so the browser-imported CA
  survives rebuilds. Don't commit it.
- **Python 3.14 breaks Type_Safe enum/dict coercion.** PEP 749 removed instance
  `__annotations__`, which `osbot_utils` reads in `Type_Safe__Convert`. Symptom:
  `invalid type for attribute '...' Expected '<enum ...>' but got '<class 'str'>'`.
  Fix belongs upstream in OSBot-Utils; locally, run on 3.12/3.13.
- **Interceptor only forwards `GET` + `text/html`** to the service; everything
  else passes through untransformed.
- **Upstream debug headers are opt-in.** `process_request` only adds the
  `x-mgraph-proxy`/`x-request-id`/`y-version-*`/etc. headers when the request
  carries `mitm-debug=true` (cookie) or `x-mitm-debug: true` (header). Keep them
  gated — they fingerprint the proxy to every upstream site.
- **`inject` mode needs S3** (`CACHE__SERVICE__BUCKET_NAME` + AWS creds); scripts
  live at `s3://{bucket}/{namespace}/inject/data/sites/{domain}/filter.js`.
- Env files with secrets (`.env`, `.local-server.env`, `.build.env`) are
  gitignored; commit only the `*.example` templates.

## Secrets

Never commit API keys, AWS creds, or the `certs/` CA. Use the `.example`
templates and environment variables.
