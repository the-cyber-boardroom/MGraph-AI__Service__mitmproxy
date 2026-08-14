# Handoff — content-proxy S3 read and greenfield stub investigation

**Date:** 2026-08-14  
**Primary repository:** `MGraph-AI__Service__mitmproxy` (`dev`)  
**Goal:** establish whether the shipped inject service can mistake a transient
cache-service/S3 read failure for a genuinely missing domain and overwrite a
real filter with `EMPTY_STUB`; then write up or fix the behaviour with tests.

## Executive summary

The intended shipped design has **no per-domain in-process script cache**.
`Proxy__Inject__Service.resolve_script()` asks the Cache service for
`sites/<domain>/filter.js`; that Cache FastAPI uses an S3 backend. If the read
returns `None`, the inject service writes and returns the 68-byte greenfield
stub.

Two distinct incidents produced the same visible symptom:

1. **Sky News, 2026-08-13, before the debug patch:** Firefox appeared to receive
   the 68-byte stub after the full filter had been pushed. The worklog suspected
   `_load_from_cache()` returned `None` without an exception while the canonical
   S3 object remained full. That S3-read-error theory was **never proven**:
   Firefox/proxy provenance was later found to be mixed, and a fresh Firefox on
   the correct content-proxy EXT received the full filter without another push.
2. **Sky Sports, 2026-08-14:** this was proven and had a different cause.
   Yesterday's live diagnostic patch was still resident in `cp-mitm-service`.
   It re-enabled `_script_cache`, cached stubs, and exempted only `sky.com`.
   Restoring the shipped `Proxy__Inject__Service.py` and restarting that
   container fixed Sky Sports immediately.

Do not conflate the proven Sky Sports residual-patch failure with the unresolved
original Sky News observation.

## Intended architecture (confirmed from source)

Primary code:

- `mgraph_ai_service_mitmproxy/service/proxy/inject/Proxy__Inject__Service.py`
- `mgraph_ai_service_mitmproxy/fast_api/Mitmproxy__Service__Fast_API.py`

Supporting repositories:

- `MGraph-AI__Service__Cache__Client` — transport/client contract, especially
  `Cache__Service__Client__Data__Retrieve.py` and
  `register_cache_service.py`
- `MGraph-AI__Service__Cache` — S3-backed Cache FastAPI route
  `Routes__Data__Retrieve.data__string__with__id_and_key`
- `corporate_infrastructure` — content-proxy appliance/deployment and guardian
- `akeia-cache-editor-experiments` — operational evidence and publisher
  worklogs, not the owner of `Proxy__Inject__Service`

The shipped resolution path is:

1. `_get_or_create_cache_id()` caches only the shared **cache ID** in memory.
2. `_load_from_cache(domain)` calls the Cache client for
   `sites/<domain>/filter.js`.
3. The client returns text only for HTTP 200 with non-empty body; **all other
   statuses and empty 200 bodies collapse to `None`**.
4. `resolve_script()` treats every `None` as “domain does not exist”, calls
   `_store_to_cache(domain, EMPTY_STUB)`, prints “Created inject stub”, and
   returns the stub.

`run_in_memory=True` is confusingly named: it registers an in-process Cache
FastAPI/TestClient. On the appliance that Cache API is configured with
`CACHE__SERVICE__BUCKET_NAME=akeia--mgraph-ai-cache`, so filter contents are
still backed by S3. It is not the commented-out `_script_cache` dictionary.

## What Sky News actually established yesterday

Source:
`akeia-cache-editor-experiments/docs/worklogs/260813/worklog_skynews_260813.md`,
especially Entries 16–28.

Evidence that was real:

- Canonical Cache service/S3 held the full `sky.com` filter throughout
  (~249 KB).
- A headed Firefox document showed HTTP 200, `x-mitm-inject-size: 68`, no
  `__skynewsFilter`.
- FastAPI logs contained both:
  - a 200 Sky response injected with 68 bytes; and
  - a 403 Sky response loaded from S3 and injected with ~249 KB.
- The “Created inject stub” message is unconditional after a miss; it did not
  prove the full canonical object was overwritten.
- Direct idle FastAPI probes, including a 2.5 MB body, read the correct S3 key
  and returned the full filter.

What was inferred but **not proven**:

- Entry 21 said the 200 path's `_load_from_cache()` returned `None` without a
  logged error. That was inferred from the stub branch, not captured as an HTTP
  status/body from the original code.
- After sky-only logging was added, the Firefox request that still displayed a
  stub did **not enter the patched FastAPI process at all**: there was no
  `POST /proxy/process-response`, no `resolve_script` log, and no S3 GET log.
- The Firefox profile was later shown to have classifier-proxy pinning, while
  other evidence came from content proxy EXT.
- A fresh Firefox on the correct content proxy received the full Sky News
  filter without a re-push.

Therefore the statement “content-proxy FastAPI failed to read the existing Sky
filter from S3” remains a hypothesis, not a settled fact.

## Repo-first investigation results — 2026-08-14

### Verdict

The shipped control flow has a **proven overwrite capability**:

1. an inject-cookie request reaches `resolve_script()`;
2. `_load_from_cache()` catches a read exception and returns `None`;
3. `resolve_script()` treats that `None` as a true miss;
4. `_store_to_cache(domain, EMPTY_STUB)` writes to the same
   `(cache_id, sites/<domain>/filter.js)` location.

A deterministic stateful unit test began with a full filter in the backing
store, raised a transient read exception while that object still existed, and
confirmed that the shipped policy replaced the same key with `EMPTY_STUB`.

This proves **“the code can do this.”** It does **not** prove **“this is what
happened to Sky News.”** The original Sky request did not capture the read
status/exception, cache ID, or successful write. Later provenance was mixed,
and a correctly routed fresh Firefox received the full filter without a push.

### Required cookie lifecycle

Characterization tests now cover the intended lifecycle:

- new site, no `mitm-mode=inject` cookie → no resolve, cache read, write, stub,
  or injection;
- new site, inject cookie, true miss → write and inject `EMPTY_STUB`;
- replace that S3 stub with a full filter → the next inject-cookie request
  reads and injects the full filter (there is no active per-domain script
  cache in shipped source);
- non-HTML responses do not enter inject.

Two existing exceptions are now explicit:

- `www.bbc.co.uk` forces inject without the cookie;
- inject-cookie HTML is processed regardless of upstream status, including
  403 responses.

These are characterization facts, not changes made by this investigation.

### Live Cache and Cache Client path

Both supporting repositories are used by the live content-proxy path:

- `MGraph-AI__Service__Cache__Client`
  `register_cache_service__in_memory()` constructs and registers an in-process
  `Cache_Service__Fast_API` using Starlette TestClient transport.
- That Cache FastAPI is supplied by `MGraph-AI__Service__Cache`.
- “In memory” describes the **client transport**, not the storage backend.
  `Cache__Config` selects `CACHE__SERVICE__STORAGE_MODE` when explicit,
  otherwise S3 when AWS credentials are detected, otherwise memory.
  `CACHE__SERVICE__BUCKET_NAME` names the bucket only after S3 mode is chosen.

The inject-relevant outcomes are:

| Backend / route outcome | Cache Client result | Inject result |
| --- | --- | --- |
| found, non-empty string (HTTP 200) | script text | inject script; no write |
| true miss (HTTP 404 empty) | `None` | write/inject stub |
| found empty string (HTTP 200 empty) | `None` | write/inject stub |
| non-200 response, including 5xx | `None` | write/inject stub |
| in-process S3 exception / timeout | exception reaches `_load_from_cache()` | caught as `None`; write/inject stub |

The last row follows from the in-process TestClient path and
`Storage_FS__S3` having no local exception translation around the read.
Whether the lower `osbot_aws.S3` wrapper has any additional soft-fail path
still requires direct runtime evidence; it is not needed to prove the
exception-to-stub control flow.

### Provenance and validation

Investigation branch used consistently in all three repositories:

`investigate/inject-stub-s3-miss-260814`

Only `MGraph-AI__Service__mitmproxy` has file changes. Cache and Cache Client
remain read-only.

Mitmproxy source baseline:

- branch base: `dev`;
- commit: `4cdf8f1a737184717cffec2d7effde3bae1bd4b8`;
- runtime and `pyproject.toml` versions: `v0.8.36` (equal);
- `Proxy__Inject__Service.py` SHA-256:
  `d7da8b20aa4830ed952c2c9d1bb034f1143d0e9d59082180becffd00ab23a3b3`;
- `Proxy__Response__Service.py` SHA-256:
  `ee08675865f34bf4245c3e71ff9f3ae87b0b6ab7069c1d82511dddb43f4bc978`.

Local test environment resolved:

- `mgraph-ai-service-cache==0.14.0`;
- `mgraph-ai-service-cache-client==0.33.0`;
- `osbot-fast-api==0.39.0`;
- `osbot-fast-api-serverless==1.35.0`.

These local versions match the committed lock but do not certify the running
appliance: the Dockerfile uses `pip install -e .` with wildcard dependencies
and does not install from `poetry.lock`.

Validation:

- new inject lifecycle tests: **16 passed**, plus 4 subtests;
- full inject + response suites: **50 passed, 6 skipped**;
- Cache string-retrieve route tests: **24 passed**;
- Cache Client data-retrieve tests: **35 passed**;
- full mitmproxy unit suite: **550 passed, 41 skipped, 1 unrelated failure**
  (`test_process_show_command__wcf_command`, live WCF response returned
  `None`); the process also remained alive after its pytest summary and was
  stopped.
- IDE lint diagnostics: no errors in the new test files.

No local `cp-mitm-service` container was running for a source-hash comparison,
and Docker Hub did not expose `diniscruz/mgraph-ai-service-mitmproxy:v0.8.36`
at investigation time. Therefore no new claim is made that the current live
container hash equals this checkout. The earlier on-box evidence in this
handoff remains the live provenance record.

### Stop point before a production fix

No production code changed. The next design must preserve:

- no inject cookie → no stub/cache mutation;
- inject cookie + **confirmed true miss** → create and inject the stub;
- replacing the stub with a full S3 filter → serve that full filter on the
  next request;
- read error, timeout, empty/corrupt response, or uncertain cache ID → never
  write a stub.

Candidate repo-only mechanisms include a status-aware existence check or raw
request result before stub creation. A typed Cache Client result may be cleaner
but would expand the production change into `MGraph-AI__Service__Cache__Client`.
That choice must be reviewed separately.

The reviewed fix specification is now:

`docs/plans/INJECT_CACHE_READ_RETRY_FIX_260814.md`

It specifies a backwards-compatible TypeSafe Cache Client result, exactly one
retry owned by mitmproxy, confirmed-miss-only stub creation, and truthful
read/write error handling. Matching impact notices exist in
`MGraph-AI__Service__Cache` and `MGraph-AI__Service__Cache__Client`.

## What the 2026-08-13 live patch changed

Original container file was preserved at:
`/tmp/akeia-inject-bak-260813/Proxy__Inject__Service.py`.

The patch:

- enabled `_script_cache`;
- cached every returned script, including `EMPTY_STUB`;
- skipped that memory cache only for `sky.com`;
- retried an S3 read once on `None`;
- added sky-only raw GET tracing;
- added non-2xx inject suppression and a `sky.com` boot-warm in
  `Proxy__Response__Service.py`.

This patch made Sky News repeatedly read S3 but created a deterministic stale
stub for every other new domain. Sky Sports was the first such domain. The
patched inject file was preserved on the host at
`/tmp/akeia-inject-patched-260814/` before restoration.

Current live state:

- `Proxy__Inject__Service.py`: restored to shipped source; container restarted.
- `Proxy__Response__Service.py`: still locally patched with non-2xx skip,
  `host=` passthrough, and Sky boot-warm.
- Do not force-recreate the container before preserving/reviewing that remaining
  patch.

## Original investigation plan (executed repo-first)

1. Reproduce locally in `MGraph-AI__Service__mitmproxy`; do not use a publisher
   or live proxy first.
2. Add direct `resolve_script()` tests. Existing inject tests mock
   `resolve_script()` and do not cover cache lookup, miss classification, or
   stub writes.
3. Cover at least:
   - existing full filter → returned, never written;
   - true 404 → stub written once and returned;
   - 500/timeout/exception → **must not write a stub**;
   - HTTP 200 empty body → explicitly decide whether corruption/error or
     missing;
   - transient first failure then success → no stub overwrite;
   - existing stub → returned as the expected greenfield proof.
4. Stop collapsing every non-200 into `None`. The Cache Client currently loses
   the distinction between 404 and transport/server failure. Decide whether to:
   - return a typed result/status from `MGraph-AI__Service__Cache__Client`; or
   - perform an existence check / raw request in the inject service.
5. Make stub creation conditional on a **confirmed 404 only**. Fail open for
   page delivery on cache errors, but do not mutate S3.
6. Decide whether retry-once is still useful after status-aware handling.
7. Review and either upstream or remove the remaining local
   `Proxy__Response__Service.py` patch (especially non-2xx inject suppression).
8. Write a durable incident note distinguishing:
   - intended greenfield stub creation;
   - unproven Sky News S3-read theory;
   - proven Sky Sports residual debug-patch failure.

## Constraints

- Do not re-push `sky.com` or `skysports.com`.
- Do not curl Sky, Sky Sports, or Daily Mail as browser verification; Akamai
  returns misleading 403 pages to non-browser clients.
- Do not restart Firefox or `cp-mitmproxy-ext`.
- Diff live container files against image/repository source before drawing
  architectural conclusions.
- Use IAM `akeia-filter-analysis` first. SSO requires James's explicit one-off
  approval and must never be added to scripts.

## Production-fix definition of done (not yet met)

- Current characterization tests prove the opposite: a transient read failure
  **can** create/overwrite a filter with the greenfield stub.
- A later fix must add regression tests proving that transient failures do not
  write, while confirmed true misses still create/inject the stub.
- Missing versus error must be represented explicitly; it is not today.
- Any production code fix lands in the correct owning repository/repositories,
  not as a writable-container patch.
- Remaining live `Proxy__Response__Service.py` drift is upstreamed or removed.
- The incident write-up clearly labels evidence, inference, and retractions.
