# Worklog — content-proxy inject retry live test — 2026-08-14

Owning repo: `MGraph-AI__Service__mitmproxy`. Branch:
`investigate/inject-stub-s3-miss-260814`.

## Objective

Temporarily install the already-implemented Cache/S3 retry fix into the
running content-proxy `cp-mitm-service` container and prove the live process
behaves as specified.

**This is a disposable writable-layer test installation.** It is not a
deployment path. The patch is lost on container recreation, guardian action,
AMI replacement, or instance rotation. Installer and test helpers live only
in `Akeia/tmp/` and must not be committed.

Canonical spec:
`docs/plans/INJECT_CACHE_READ_RETRY_FIX_260814.md`

Investigation handoff:
`docs/handoffs/content_proxy_inject_s3_stub_investigation_260814.md`

## Auth (one-off)

James explicitly authorised one-off use of AWS SSO profile
`Dev-504558652080` for this inspection, patch, and test only.

- Account: `504558652080`
- Identity: `arn:aws:sts::504558652080:assumed-role/AWSReservedSSO_AdministratorAccess_a9a38db944933113/JamesD`
- Region: `eu-west-2`
- Session was already valid; `aws sso login` was not re-run
- SSO was not embedded in scripts, configuration, documentation defaults, or
  automation

## Resolved instance

Historic ID `i-0293aa92fadff83da` is still current.

| Field | Value |
| --- | --- |
| Instance ID | `i-0293aa92fadff83da` |
| Name tag | `akeia-mitm-proxy-v2-dev` |
| ASG | `akeia-content-proxy-v2-dev` |
| State | running |
| Launch | 2026-07-08T14:16:44Z |
| AMI | `ami-0c3ec31eecc8f2a10` |
| Private IP | `172.31.38.26` |
| Public IP | `18.175.172.252` |
| SSM | Online (agent 3.3.4624.0) |
| DNS | `mitmproxy.dev.akeia.ai` |

## Container / image provenance (before mutation)

Captured 2026-08-14T13:33:31Z.

| Field | Value |
| --- | --- |
| Container | `cp-mitm-service` `cf981fdd2bba0fb32d8b71805f78a9b1f30c27fb04e2dc099df39c804bfab5c7` |
| Image | `diniscruz/mgraph-ai-service-mitmproxy:latest` |
| Image ID | `sha256:edeb7765bbc94d6e2e725f9edecf13499a962273a4945faa8ab6f86054bb4eb0` |
| Digest | `sha256:ada9e567e436f03ef9add6f4a9e7427d611ea9d2479b9df2e24a54d2d54ea6a6` |
| Image created | 2026-06-18T23:16:13Z |
| Container created | 2026-06-24T01:49:29Z |
| Started (pre-test) | 2026-08-14T10:26:37Z |
| Python | 3.12.13 |

Other containers left running (EXT not restarted):

- `cp-mitmproxy-ext` Up 25h, started 2026-08-13T12:34:29Z
- `cp-mitmproxy-int` Up 5 weeks
- `cp-vault-app` Up 5 weeks
- `cp-sg-playwright` Up 5 weeks
- `akeia-browser-tools` Up 5 weeks (healthy)

## Installed dependency versions (live)

| Package | Version |
| --- | --- |
| `mgraph_ai_service_mitmproxy` | 0.8.33 |
| `mgraph_ai_service_cache` | 0.14.0 |
| `mgraph_ai_service_cache__client` | **0.33.0** |
| `osbot_utils` | 3.74.0 |
| `osbot_fast_api` | 0.39.0 |
| `osbot_fast_api_serverless` | 1.35.0 |
| `osbot_aws` | 2.39.10 |
| `fastapi` | 0.137.2 |
| `uvicorn` | 0.49.0 |
| `starlette` | 1.3.1 |

Feature-branch Cache Client is based on 0.31.1. Live image resolved 0.33.0
via wildcard install. Live `Cache__Service__Client__Data__Retrieve.py` and
`Cache__Service__Client__File__Retrieve.py` hashes matched git tag `v0.33.0`
exactly. **The whole Client package was not replaced.** Only new schemas and
two additive result methods were installed.

Live inject source was older than investigation checkout `d7da8b20`: it still
used `html.lower().rfind('</body>')`. Replacing `Proxy__Inject__Service.py`
with commit `f354b4d` also brings the `re.finditer` body-close fix from that
branch. Response-service drift was left untouched.

## Before / after hashes

| File | Before | After |
| --- | --- | --- |
| `Proxy__Inject__Service.py` | `03c4fc46460fdbdad0c5744ecf0b87617c1441b0d6796b1c19e7abfb0138fa46` | `625a49be0ddf6fb2795641bfd4222f4e58e84af2bb2a09a7e2635e7358fdc46f` |
| `Proxy__Response__Service.py` | `c18e180d8c855eb40daab503fa241cd1563c2b724e556a5478b1253f223042c9` | **unchanged** |
| Data retrieve | `93141d15308636d9d70ec20c930bb92dbe600ea4292ad9dfcf1d8e5e38bb387e` | `3d83b3d21157fc641aff44e1a4e1ae7b96849a6c7a87013395c7108a85e98d35` |
| File retrieve | `3ade6768c26f751e38c525169fd7b3939dfc5e5688ec52ecf7fa49712a4bf977` | `a01251bb17ab008ea9530467a8a925cb16a21b7a000008e0dedb3250a6b2a085` |

Created (did not exist before):

| File | SHA-256 |
| --- | --- |
| Cache Client `Enum__Cache__Read__Status.py` | `6cb5425968953bf50c7fd7804376b120d3daac03425e42e89b80910578f00dbd` |
| `Schema__Cache__String__Read__Result.py` | `3502a0696577bfa488a6ef96391bdaee87868c47c46021af18f96b826b53bcd2` |
| `Schema__Cache__Id__Read__Result.py` | `8d0b27a1e50b4dc93a0c9f6eacf9d2c027489a4b97254e5357f2d83582420204` |
| Inject `Enum__Inject__Script__Load__Status.py` | `8849890259e71c4f951d9ac82ce5e44f1d1fcf5e70fe38a80aac6821a8c6aabd` |
| `Schema__Inject__Script__Load__Result.py` | `71881b6e4f5bd71cb3fb46c24b2f756d74dd46129533aa03796922e0587b0438` |
| Inject `schemas/__init__.py` (empty, live 3.12 package marker) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Data retrieve after-hash equals feature-branch file `05e58c0`. File retrieve
after-hash differs from the feature-branch file because the live package is
0.33.0; only the additive method and imports were inserted.

## Exact files modified

Replaced:

- `/app/mgraph_ai_service_mitmproxy/service/proxy/inject/Proxy__Inject__Service.py`

Patched additively (existing methods retained):

- `.../Cache__Service__Client__Data__Retrieve.py` — added `data__string__result__with__id_and_key`
- `.../Cache__Service__Client__File__Retrieve.py` — added `retrieve__hash__cache_hash__cache_id__result`

Created: the six schema files listed above.

**Not modified:** `Proxy__Response__Service.py` (non-2xx skip, `host=`
passthrough, Sky boot-warm all still present).

## Backup and rollback

- Fresh backup: `/tmp/akeia-inject-retry-bak-260814/` inside `cp-mitm-service`
  (relative paths preserved; `manifest.json` recorded)
- Host copies of yesterday’s patched files remain at
  `/tmp/akeia-inject-patched-260814/` and were not used
- Payload (ephemeral, not in Git): `/tmp/akeia-inject-retry-payload-260814/`
  on host and in the container
- Laptop helpers (not in Git):
  - `/Users/james/programming/Akeia/tmp/patch_content_proxy_inject_retry_260814.py`
  - `/Users/james/programming/Akeia/tmp/test_content_proxy_inject_retry_260814.py`
  - `/Users/james/programming/Akeia/tmp/capture_content_proxy_inject_provenance_260814.sh`

Rollback (restore hashes to before-state, then restart FastAPI only):

```bash
docker exec cp-mitm-service python3 /tmp/akeia-inject-retry-payload-260814/patch_content_proxy_inject_retry_260814.py rollback
docker restart cp-mitm-service
```

Do not `docker compose up --force-recreate` — that would drop the remaining
response-service drift.

## SSM command IDs

| ID | Purpose | Result |
| --- | --- | --- |
| `e2b58546-01f2-46f9-99b3-ae208b424177` | Provenance v1 | Failed (docker inspect Health template) |
| `696794f9-c26f-48a1-a86f-c8ad74ea4312` | Provenance v2 | Success |
| `68255279-b227-4062-888e-75426a773ac5` | Fetch live sources (truncated) | Partial |
| `49dc1e4b-36fa-4286-a6b9-822a476d8ab3` | Fetch live Data retrieve | Success |
| `fda37e5e-614a-401b-a324-007307d50438` | Fetch live File retrieve | Success |
| `1019b7df-d162-42e5-8a9b-c6ee1cb3cbcb` | Verify `Safe_UInt` / `Cache_Id` | Success |
| `b846d3d4-3d8d-4782-82de-c58df83bc9a2` | Transfer payload + apply | Success `APPLY_OK` |
| `674fef34-1c85-44f2-b08d-0bd5cc08b322` | Restart `cp-mitm-service` only | Success `STARTUP_OK` |
| `4513a25c-7fca-4bf6-a7f7-16cd203c450e` | Deterministic tests | Failed overall (test 07 only) |
| `e537840d-cf28-484d-ab9b-aabd03789366` | Health / hashes / manifest | Success |

## Service restart and health

- Restarted **only** `cp-mitm-service` (`cf981fdd2bba`). RestartCount 0.
- Started 2026-08-14T13:39:47Z, pid 4167466
- `cp-mitmproxy-ext` still running from 2026-08-13T12:34:29Z
- Uvicorn: `Application startup complete` / `Uvicorn running on http://0.0.0.0:10011`
- No import errors
- New status/retry schemas import
- Existing response-layer patch still present
- `/docs` HTTP 200; `/info` and `/health` HTTP 401 (auth gate, service is up)
- Boot-warm (existing response patch) loaded `sky.com` **270,472 chars** from
  S3 — full filter HIT, not `EMPTY_STUB`

## Deterministic test results

In-container unittest against the patched modules. Store boundary mocked.
Domain `example-retry-test.invalid`. No publisher objects written.

| Case | Result |
| --- | --- |
| 1. ERROR then HIT — two reads, full script, zero writes | PASS |
| 2. ERROR then ERROR — two reads, empty result, `_store_to_cache` never called | PASS |
| 3. Confirmed MISS — one read, one mocked stub-store, `EMPTY_STUB` returned | PASS |
| 4. Empty HTTP 200 — ERROR, one retry, no write | PASS |
| 5. Cache-ID lookup error twice — no parent create, no stub write | PASS |
| 6. Response-layer patch still present | PASS |
| 7. Live `theguardian.com` HIT via a fresh `Proxy__Inject__Service()` | FAIL (0 chars) |

Test 07 failed because a newly constructed service in `docker exec` does not
share the running FastAPI process Cache config (`ValueError` on cache-id
lookup, then `CACHE_ID_UNAVAILABLE`). `_store_to_cache` was mocked, so this
could not mutate S3. The running process already proved a live full-filter
HIT: boot-warm `sky.com` 270,472 chars, no stub write. Test 07 was **not**
retried against a real publisher cache.

Firefox headed verification was **not** performed. EXT Firefox was not
restarted.

## S3 objects

**No real Cache/S3 publisher objects were written.** Confirmed MISS used a
mocked store. Test 07 store was mocked. FastAPI logs since restart show the
Sky boot-warm HIT only; no live `Created inject stub` from the Uvicorn
process.

## Final live state

**Patched** (not rolled back). Writable layer only. Lost on rotation or
container recreation.

## Next durable CI / deployment action

1. Release Cache Client with the additive typed-result methods (own SemVer
   SoT; do not lockstep with mitmproxy).
2. Constrain the mitmproxy image to a Client version that includes that API.
3. Ship mitmproxy `f354b4d` (or successor) through the normal image build —
   not a writable-layer copy.
4. Review or upstream the remaining live `Proxy__Response__Service.py` drift
   (non-2xx skip, `host=` passthrough, Sky boot-warm) before any
   force-recreate.
5. Do not treat this test install as the production fix definition of done.

## Git

Installer and test scripts were not staged or committed. Worklog and handoff
are the legitimate PR evidence; ACP only if James asks.
