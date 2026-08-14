# Inject cache read retry and error-handling fix

**Date:** 2026-08-14  
**Status:** Proposed implementation  
**Branch:** `investigate/inject-stub-s3-miss-260814`

## Purpose

Preserve the existing inject lifecycle while preventing a temporary Cache/S3
read failure from overwriting a real filter with `EMPTY_STUB`.

Required behaviour:

- no `mitm-mode=inject` cookie → no inject cache read or write;
- inject cookie + existing filter → inject the filter;
- inject cookie + confirmed new-site miss → create and inject `EMPTY_STUB`;
- inject cookie + temporary read error → retry once;
- retry succeeds → inject the recovered filter;
- retry still fails or remains uncertain → do not write and do not inject for
  that request;
- the page must still be returned normally.

There is no transient stub, banner, or additional HTML payload in this fix.

## Why this is needed

The current `Proxy__Inject__Service` reduces all of these outcomes to `None`:

- confirmed 404;
- empty HTTP 200 response;
- HTTP 5xx;
- timeout or other exception;
- unavailable or uncertain cache ID.

`resolve_script()` then treats every `None` as a new site and attempts to store
`EMPTY_STUB`. A single temporary failure can therefore become a persistent
site-filter outage.

The investigation tests prove that this overwrite path exists. They do not
prove it caused the earlier Sky News observation.

## Proposed design

### 1. Preserve status in Cache Client without breaking existing callers

Add new status-aware methods to
`MGraph-AI__Service__Cache__Client`. Do not change the return contract of the
existing methods.

Follow the existing one-class-per-file and `Type_Safe` conventions:

- `Enum__Cache__Read__Status`
  - `HIT`
  - `MISS`
  - `ERROR`
- `Schema__Cache__String__Read__Result(Type_Safe)`
  - `status`
  - `value`
  - `status_code`
  - `error_type`

Add a new string retrieval method alongside
`data__string__with__id_and_key()`:

- HTTP 200 with non-empty text → `HIT`;
- HTTP 404 → `MISS`;
- HTTP 200 with empty text → `ERROR`;
- any other HTTP status → `ERROR`;
- transport/server exceptions remain exceptions for the caller to handle.

The existing `data__string__with__id_and_key()` remains unchanged for
backwards compatibility.

The cache-entry lookup used by `_get_or_create_cache_id()` needs the same
status-preserving principle: create the shared inject entry only after a
confirmed miss, never after an exception or ambiguous client `None`.

### 2. Represent inject load outcomes explicitly

In `MGraph-AI__Service__mitmproxy`, use a local TypeSafe result rather than
returning `Optional[str]`:

- `Enum__Inject__Script__Load__Status`
  - `HIT`
  - `MISS`
  - `ERROR`
- `Schema__Inject__Script__Load__Result(Type_Safe)`
  - `status`
  - `script`
  - `attempts`
  - `error_type`

Keep the current file/class naming style and use `@type_safe` where the
surrounding service uses it. Do not introduce untyped dictionaries for the
result contract.

### 3. Retry exactly once

`_load_from_cache()` performs:

1. first read;
2. return immediately on `HIT`;
3. return immediately on confirmed `MISS`;
4. retry once on `ERROR` or an exception;
5. return the second result;
6. if the retry is also `ERROR`, return an explicit error result.

No loop, exponential backoff, sleep, or further retries are part of this fix.
The retry should be immediate so a transient failure has one chance to recover
without materially delaying the page.

### 4. Mutate only after confirmed absence

`resolve_script()` handles the typed result:

- `HIT` → return the full script;
- `MISS` → store `EMPTY_STUB`;
  - store succeeds → return the stub for injection;
  - store fails/throws → return `''` and report the write failure;
- `ERROR` → return `''` and never call `_store_to_cache()`.

Returning `''` already causes `inject_script_into_html()` to leave the HTML
unchanged. It does not remove CSP headers or add an inject script.

Apply the same rule to `_get_or_create_cache_id()`:

- cached ID → use it;
- confirmed missing shared entry → create it;
- lookup error after one retry → return an error/no ID and perform no create.

## Error handling and logs

Keep the colleague's existing `print(...)` logging style, but make messages
truthful and outcome-specific:

- read attempt 1 failed, retrying once;
- read recovered on attempt 2;
- read failed after 2 attempts, no cache write;
- confirmed miss, creating stub;
- stub store succeeded;
- stub store failed, no stub injected.

Catch expected timeout, connection, client-request, and Cache/S3 exceptions at
the narrow read boundary. Do not spread broad `except Exception` handling
through the service. If the in-process third-party boundary makes a broader
catch unavoidable, keep it in one method, document why it is required, and
convert it immediately into the typed `ERROR` result. Unexpected programming
errors must not be mislabeled as `MISS`.

Retry reads only. Never retry a stub write automatically because its first
outcome may be uncertain.

Do not print “Created inject stub” unless the store call reports success.

Do not include credentials, response bodies, filter contents, or stack traces
in normal production logs. Include domain, attempt number, safe status, and
exception class only.

## End-user behaviour

The single retry protects against a short-lived read problem. If the retry
succeeds, filtering continues normally and the user sees no interruption.

If both attempts fail:

- the stored filter remains intact;
- the requested page still loads;
- injection is skipped only for that request;
- the next request tries the cache again.

This is safer than turning one temporary read failure into a persistent broken
filter that requires an operational re-push.

## Repository responsibilities

### `MGraph-AI__Service__mitmproxy`

- own the one-retry policy;
- use explicit TypeSafe hit/miss/error results;
- create stubs only on confirmed misses;
- handle cache-ID lookup and stub-store failures safely;
- retain the cookie gate and no-active-script-cache behaviour;
- add regression tests.

### `MGraph-AI__Service__Cache__Client`

- add backwards-compatible status-preserving retrieval result methods;
- retain existing methods unchanged;
- add unit tests for 200 content, 200 empty, 404, 5xx, and exception behaviour.

### `MGraph-AI__Service__Cache`

- no production-code change is expected for this fix;
- retain the existing string-route contract:
  - found content → HTTP 200;
  - true miss → HTTP 404;
  - unhandled backend failure → error/exception, never a false 404;
- keep or extend route tests so missing and backend failure remain distinct.

## Required tests

Mitmproxy:

- no inject cookie → no cache calls;
- hit on attempt 1 → inject full filter, one read;
- error then hit → inject full filter, two reads, no write;
- confirmed miss → create/inject stub without retry;
- error then error → no write, no injection;
- empty 200 then empty 200 → no write;
- cache-ID lookup error then recovery → proceed;
- cache-ID lookup error twice → no parent entry or stub write;
- confirmed miss + stub-store failure → no stub injection;
- existing stub replaced by full filter → next request serves full filter.

Cache Client:

- new typed result preserves 200, 404, 5xx, and empty-200 distinctions;
- existing retrieval methods remain behaviourally unchanged.

Cache:

- true string miss remains HTTP 404;
- found empty string remains HTTP 200 empty;
- backend exception does not become HTTP 404.

## Compatibility and release constraints

- Do not change the existing Cache Client method signatures.
- Do not add per-domain in-process script caching.
- Do not alter cookie gating or greenfield stub semantics.
- Do not add a transient stub or user-interface payload.
- Each releasable repository keeps its own SemVer source of truth; versions are
  not coupled. Bumps happen only when the implementation is released.
- The mitmproxy Docker build must consume a Cache Client version that contains
  the new typed API; record or constrain that minimum version during release so
  the image cannot resolve an older incompatible client.

## Acceptance criteria

- A transient read failure followed by success injects the real filter.
- Two failed reads never invoke a cache write.
- Only a confirmed 404/miss can create `EMPTY_STUB`.
- A failed stub store cannot be reported or injected as a successful stub.
- Existing callers of Cache Client continue to pass unchanged.
- All three repositories' focused tests pass.
- No production container is patched manually.
