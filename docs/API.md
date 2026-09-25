# API contract

All workspace and evidence calls require `Authorization: Bearer <Supabase access token>`. The server validates the user with Supabase Auth and binds the UUID to an active membership. Never send the server secret from the browser. Mutations reject a supplied Origin that differs from the request origin. All workspace/evidence responses are private and no-store.

## Read and mutate state

`GET /api/workspace` returns the caller's role-filtered projection and `revision`. Only administrators may preview a member with `?persona=<member-id>`; actions in preview retain the actual actor.

`POST /api/workspace` uses JSON with `revision` and `action`, plus:

| Action | Required fields / notes |
| --- | --- |
| create | road, title, lat, lng, accuracy, lane, note; optional severity |
| assign | id (case), team, optional analyst member ID; Admin or own-team lead |
| transition | id, status, note; subject to stage graph and role |
| note | id, note; optional visibility = shared, otherwise internal |
| team | name; Admin |
| contract | contractor, road, scope, start/end YYYY-MM-DD, poc, email; Admin |
| member | name, email, role, team, contractor, authUserId UUID, active boolean; Admin |
| memberUpdate | memberId and all membership fields; Admin |

Transition extras: Notice prepared requires `contract` ID and `scopeConfirmed:true`; Duplicate requires `duplicateOf`; Verified closed requires `evidenceId` and `verification:"clear-pass"`. Notes require 10–2,000 characters. Requests are capped at 32 KB. Successful writes return the filtered workspace and next revision. A 409 requires reload and review before retry.

Example assignment (substitute current IDs and revision):

```json
{"action":"assign","revision":7,"id":"PL-2026-EXAMPLE","team":"Central roads","analyst":"MEMBER_ID"}
```

## Evidence

`POST /api/evidence` accepts multipart form fields: `ticket`, `revision`, `authorized=true`, `purpose` (detection/repair/verification), `capturedAt` (ISO UTC), `lat`, `lng`, `accuracy` (metres), `lane`, `quality` (clear/unclear), and `file`. `shared=on` exposes the evidence to the firm's contractor once the case is released. Contractor uploads are forced to shared repair evidence.

File limits: JPEG, PNG or WebP; 3,000,000 bytes; 40 files per case. Exact duplicate hashes in one case are rejected. Capture timestamps cannot be future or more than 30 days before case creation. Uploads to terminal cases require reopening where supported. Body/file limits are pilot controls, not a full upload-security pipeline.

`GET /api/evidence?ticket=<case-id>&id=<file-id>` returns `{ "url": "..." }` after case and sharing checks. URL lifetime is 60 seconds. File bytes are not returned inside workspace JSON.

## Errors

400 invalid input or business gate; 401 missing/invalid/unconfirmed authentication; 403 unauthorized role or scope; 404 unavailable persona; 409 revision conflict; 413 request size; 503 configuration/backend failure. Do not retry validation or permission errors as if they were transient failures. Use a fresh read after 409. The client retains unsaved fields where supported.

`GET /api/health` is unauthenticated process liveness, not an end-to-end readiness test.
