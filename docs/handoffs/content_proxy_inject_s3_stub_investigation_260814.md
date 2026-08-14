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

## Investigation plan

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

## Definition of done

- Automated tests prove a transient read failure cannot create/overwrite a
  greenfield stub.
- Missing versus error is represented explicitly.
- Any production code fix lands in the correct owning repository/repositories,
  not as a writable-container patch.
- Remaining live `Proxy__Response__Service.py` drift is upstreamed or removed.
- The incident write-up clearly labels evidence, inference, and retractions.
