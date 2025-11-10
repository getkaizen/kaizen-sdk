# Kaizen SDK Knowledge Transfer

This document captures the HTTP contract, field semantics, and noteworthy implementation details needed to build client libraries (e.g., `kaizen-client`). Use it alongside `tokens/main.py` for full fidelity.

## Base Service Facts
- **Base URL:** `http(s)://<host>/v1`. The FastAPI root `/` only returns `{"message": "Welcome to the Token Service"}` for health checks.
- **Content-Type:** All endpoints accept and return JSON. Requests must include JSON bodies (except `GET /`).
- **Auth:** Not enforced in this repo; SDKs should prepare for a future bearer token by letting callers inject headers (the service looks for `Authorization` but never validates it today).
- **Status Envelope:** Success responses follow `{"status": "success", "operation": <operation>, ...}`. Errors raise standard FastAPI/HTTPException payloads with `detail` strings.
- **Options Objects:**
  - `EncodeOptions`: `indent` (≥1, default 2), `delimiter` (one of `","`, `"\t"`, `"|"`), `length_marker` (`True`/`"#"` to include `#len` headers, `False` to omit).
  - `DecodeOptions`: `indent` (scanner indent size, ≥1) and `strict` (default `True`; toggles whitespace + count validation).

## KTOF Format Cheat Sheet
- **Objects:** encoded as `<key>: <value>` per line, with indentation controlled by `indent`. Empty dicts emit just `key:`.
- **Primitive arrays:** emit `key[#?len<delimiter?>]: value<delimiter>value...` on a single line. `length_marker=True` or `"#"` prepends `#` inside the brackets.
- **Array headers:** `[len]` optionally followed by `{field1<delimiter>field2}` for tabular objects. If a `key` exists, it prefixes the header as `key[len]:`.
- **List items:** use `- ` plus the encoded content. Nested arrays/objects under list items increase depth by 1 relative to the header line.
- **Inline strings:** left unquoted only when `tokens/shared/validation.is_safe_unquoted` returns true. Otherwise they are double-quoted with escapes handled via `escape_string`.
- **Normalization quirks:** unordered inputs (e.g., sets) become lists; dataclasses and objects with `__dict__` are converted via `vars()`. Non-finite floats become `null`. Negative zero is coerced to `0`.

## Shared Helpers & Metadata
- `_compute_stats` always compares `len(original_serialized_json)` vs `len(encoded_string)` and returns `original_length`, `optimized_length`, `reduction`, `reduction_ratio` (0 when original length is 0).
- `_serialize_for_stats` normalizes arbitrary inputs via `tokens.encode.normalize_value` and dumps them with compact separators + `ensure_ascii=False`. This ensures stats compare actual JSON bytes, not arbitrary Python objects.
- `_encode_with_options` / `_decode_with_options` wrap the library helpers and raise HTTP 400 (`Invalid encode request` / `Invalid decode request`) for `ValueError`, `TypeError`, or `SyntaxError`.
- **Auto JSON detection:** `_prepare_prompt` scans string prompts using `tokens.shared.json_detection.extract_json_blocks`. Each block:
  - Must be bracket/brace delimited and surrounded by allowed punctuation/whitespace.
  - Is re-encoded with `indent=1` before substitution.
  - Records `start_offset`, `end_offset`, previews, and byte counts inside `meta["replacements"]`.
  - `auto_detection_applied` is `True` only if the segmented version beat the plain encode; otherwise the service keeps the plain encode and strips `segments_schema`/`replacements` so clients do not misinterpret stale metadata.
- **Token stats:** `_compute_token_stats` needs `token_models`. When `tiktoken` is installed the real tokenizer is used; otherwise `_FallbackEncoder` splits on whitespace. SDKs calling `/prompts/encode` or `/optimize/request` can rely on `token_stats["raw"][model]` and `token_stats["optimized"][model]`, each containing `tokens` and `bytes`.

## Endpoint Reference

### `POST /v1/compress`
Encode arbitrary JSON into KTOF.

**Request body:**
```json
{
  "data": <any JSON-serializable value>,
  "options": {"indent": 2, "delimiter": ",", "length_marker": false}
}
```
- `options` is optional; validation occurs server-side.

**Response fields:**
- `result` – the raw KTOF string (no trailing newline).
- `operation` == `"compress"`.
- `status` == `"success"`.

**Request field details**

| Field   | Type  | Required | Notes |
|---------|-------|----------|-------|
| `data`  | any JSON-compatible value | ✅ | Normalized internally before encoding (see “KTOF Format Cheat Sheet”). |
| `options.indent` | integer ≥1 | ❌ | Overrides default indent of 2 spaces. |
| `options.delimiter` | `","`, `"|"`, or `"\t"` | ❌ | Controls delimiter for inline arrays/tabular rows. |
| `options.length_marker` | `true`, `false`, `"#"` | ❌ | When truthy, writes `[#{len}]` headers. |

### `POST /v1/decompress`
Reverse a KTOF string to JSON.

**Request body:**
```json
{
  "data": "messages[2]{role,content}:...",
  "options": {"indent": 2, "strict": true}
}
```
- `indent` tells the scanner how many spaces equal one depth level (must match what the encoder used if strict mode stays on).
- `strict` enforces: no tabs in indentation, indentation multiple of `indent`, no blank lines within arrays/objects, and exact item counts.

**Response fields:**
- `result` – decoded JSON structure (lists/dicts/primitives).
- `operation` == `"decompress"`.

**Request field details**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `data` | string | ✅ | Must be valid KTOF; multiline strings are allowed. |
| `options.indent` | integer ≥1 | ❌ | Must match the indent used during encoding when `strict` is `true`. |
| `options.strict` | bool | ❌ | Defaults to `true`; when `false`, indentation irregularities and count mismatches are tolerated. |

### `POST /v1/optimize`
Encode JSON and return stats comparing it to the normalized JSON baseline.

**Request body:** Same shape as `/compress`.

**Response fields:**
- `result` – KTOF string.
- `stats` – see “Shared Helpers”.
- `operation` == `"optimize"`.

**Extra notes**
- `stats.reduction_ratio` is a float between `0.0` and `1.0`. Negative reductions never occur because the optimized length is simply the encoded KTOF size.
- `stats.original_length` refers to the bytes of normalized JSON, not the input string length. JSON is serialized without whitespace.

### `POST /v1/optimize/request`
Legacy prompt encoder with auto-detection and optional telemetry.

**Request body:**
```json
{
  "prompt": <string|object|array>,
  "options": { ... },
  "auto_detect_json": true,
  "metadata": {"source": "foo"},
  "token_models": ["gpt-4o"]
}
```
- `prompt` can be structured JSON or plain text. Auto-detection only fires when it is a string and `auto_detect_json` is `true`.
- `metadata` is copied to `meta.client_metadata` so upstream systems can correlate requests.

**Response fields:**
- `result` – whichever of `plain_encoded` or `segmented_encoded` produced the fewest characters.
- `stats` – computed against the original serialized JSON (not the plain string) so numbers are consistent even when auto-detection rewrites strings.
- `meta` (optional) – includes `auto_detected_json`, `embedded_json_count`, `segments_schema`, `replacements`, `auto_detection_applied`, and optional `client_metadata`.
- `token_stats` (optional) – per model `tokens`/`bytes` for both `raw` (original serialized prompt) and `optimized`.

**Request field details**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `prompt` | object/array/string | ✅ | Strings get JSON auto-detection; objects/arrays skip that path. |
| `options` | EncodeOptions | ❌ | Passed directly to the encoder. |
| `auto_detect_json` | bool | ❌ | Default `true`. Disable when the prompt contains brace-heavy prose to avoid accidental rewrites. |
| `metadata` | object | ❌ | Arbitrary context; echoed under `meta.client_metadata`. |
| `token_models` | list[str] | ❌ | Each model incurs an extra encode pass (`raw` and `optimized`). |

**Response meta fields**

| Key | Meaning |
|-----|---------|
| `auto_detected_json` | `true` if any JSON blocks were discovered inside the prompt string. |
| `embedded_json_count` | Number of replacements performed. |
| `segments_schema` | Currently set to `"text_with_ktof"` when auto-detection rewrites the string. |
| `replacements` | List of objects containing offsets, original vs encoded lengths, and 80-char previews. |
| `auto_detection_applied` | `true` only when the segmented encode beat the plain encode in length. |
| `client_metadata` | Echo of the request’s `metadata`. Present even when auto-detection is disabled. |

### `POST /v1/optimize/response`
Decode a KTOF payload (typically the LLM reply) and report size deltas.

**Request body:**
```json
{
  "ktof": "...",
  "options": {"indent": 2, "strict": true}
}
```

**Response fields:**
- `result` – decoded JSON or string.
- `stats` – compares `len(ktof)` vs `len(json.dumps(decoded))`.

**Request field details**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ktof` | string | ✅ | The model’s KTOF output. |
| `options` | DecodeOptions | ❌ | Same semantics as `/decompress`. |

### `POST /v1/prompts/encode`
Preferred prompt optimizer. Adds schema hints and metadata replay support.

**Request body:**
```json
{
  "prompt": <string|object>,
  "options": { ... },
  "auto_detect_json": true,
  "schemas": {"messages": ["role", "content"]},
  "metadata": {"source": "sandbox", "agent": "census"},
  "token_models": ["gpt-4", "claude-3-sonnet"]
}
```
- `schemas` are echoed back inside `meta["schemas"]`. They do not alter encoding logic today but let clients remember table shapes.
- `metadata` behaves like `/optimize/request`.

**Response fields:**
- Same as `/v1/optimize/request`, with `operation` == `"prompts_encode"` and deterministic inclusion of `schemas` when provided.

**Additional behaviors**
- `schemas` are purely informational today. The server stores them in `meta.schemas` even when auto-detection is skipped so UIs can render table headers consistently.
- If both `schemas` and auto-detection metadata exist, both structures are merged under the same `meta` dict.

### `POST /v1/prompts/decode`
Decode prompts and optionally replay metadata.

**Request body:**
```json
{
  "ktof": "...",
  "options": {"indent": 2, "strict": true},
  "replay_meta": {"source": "cache"},
  "metadata": {"source": "sandbox"}
}
```
- `replay_meta` is merged into the returned `meta` (shallow copy). Keys like `client_metadata` are still reserved for the metadata echo from the request body.
- `metadata` again flows into `meta.client_metadata`.

**Response fields:**
- `result` – decoded JSON/string.
- `stats` – same computation as `/v1/optimize/response`.
- `meta` (optional) – contains replay metadata and echoed client metadata.

**Request field details**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ktof` | string | ✅ | Data previously returned by `/prompts/encode` or `/optimize/request`. |
| `options` | DecodeOptions | ❌ | Defaults match the encoder defaults. |
| `replay_meta` | object | ❌ | Arbitrary context to stitch downstream events (e.g., `{"execution_mode": "cached"}`). |
| `metadata` | object | ❌ | Echoed as `meta.client_metadata` so telemetry stays aligned. |

## Error Shapes & Validation Notes
- Request validation happens via Pydantic models. Missing required fields trigger HTTP 422 responses with detailed errors (e.g., `indent` being 0).
- Encoding/decoding issues (invalid delimiter, malformed KTOF) trigger HTTP 400 with `detail` describing the failure. SDKs should surface `detail` and HTTP status.
- `tiktoken` loading failures inside `_resolve_encoder` raise HTTP 500 with `Unable to load tokenizer` message; clients may retry without `token_models` or install `tiktoken` in the service environment.

## Implementation Nuances Worth Mirroring in SDKs
- **Normalization side effects:** Stats always compare against normalized JSON, so SDK helpers should not try to recompute stats locally—they might not match server decisions involving auto-detection or sets/dataclasses.
- **Length marker semantics:** Passing `length_marker=True` yields headers like `[#{len}]`. Set `length_marker="#"` for compatibility with other languages.
- **Indent coupling:** `DecodeOptions.indent` must match the encoding indent whenever `strict` is true. SDKs should default to 2 to align with server defaults.
- **Metadata lifecycle:** Any `metadata` object supplied to `/prompts/*` or `/optimize/request` is returned verbatim under `meta.client_metadata` and also available on `/prompts/decode` when re-sent. This lets SDKs attach session info without storing it separately.
- **Auto-detect guard rails:** Detection only runs for string prompts. Structured prompts (dict/list) skip `_prepare_prompt` entirely; SDKs shouldn’t expect `meta.auto_detected_json` to exist in those cases.
- **Token stats cost:** Computing tokens requires encoding both raw and optimized strings for every requested model. SDKs should make `token_models` opt-in to avoid extra CPU unless savings telemetry is needed.
- **Schema hinting:** The backend does nothing with `schemas` beyond echoing them back; SDKs can treat them as opaque metadata and piggyback domain-specific hints if needed.
- **Replay metadata ordering:** When both `replay_meta` and `metadata` are provided to `/prompts/decode`, `meta` will contain keys from `replay_meta` plus `client_metadata`. Later keys override earlier duplicates, so avoid reusing the `client_metadata` key inside `replay_meta`.

This reference, plus the inline comments in `tokens/main.py`, should provide enough fidelity to implement feature-complete client libraries.
