# PaveLedger deployment and operations guide

Vercel export • Version 2.0 • 25 September 2026

This package reconstructs the accessible PaveLedger project files and supplies an operational pilot for one municipal workspace. Deploy the paveledger-vercel folder. The original business documents and source snapshot are preserved separately.

## What is ready

The Next.js app includes Supabase sign-in, server-enforced membership and case permissions, team and analyst assignment, investigation stages, contractor progress, independent review, private photo evidence, reopening, audit history and role-filtered dashboards. SQL migrations create its database table and private evidence bucket.

## What still needs integration

Fleet ingestion, live AI detection, automatic contractor email, delivery receipts, scheduled reminders, geospatial warranty matching, subscriptions and a production-grade immutable audit service are not connected. A notice is prepared inside the app; it is not sent. Photo GPS, capture time and lane are entered by the operator and are not device-attested.

## Package map

| Location | Purpose |
| --- | --- |
| paveledger-vercel/ | Deployable source, dependency lock, configuration, SQL, tests and Markdown guides. |
| originals/ | Business plan, brochures, engineering design, financial workbook, logo, overview, historical domain research and original archives. |
| guides/ | This guide in Word, PDF and Markdown. |
| MANIFEST_SHA256.txt | Checksums for every delivered master-package file except the manifest itself. |

The earlier Vercel ZIP is truncated. It is retained as DAMAGED_REFERENCE for provenance only. The rebuilt project restores missing assets from the saved site source. No secrets, passwords or dependency folders are bundled.

A complete live Sites database export was unavailable: the database viewer truncated its JSON record. This package is not a backup of live operational data. Follow the migration instructions on page 11 before replacing the existing site.

Reading order: setup 2–4; roles 5; investigation 6–7; evidence and architecture 8–10; operations 11; acceptance and troubleshooting 12; references 13.

# 1. Prepare the deployment

## Choose the deployment boundary

Use one Vercel project and one dedicated Supabase project per municipality for this pilot. WORKSPACE_ID identifies one workspace; it is not a customer-selectable tenant boundary. Do not use this version as a shared multi-municipality SaaS installation.

Create a private Git repository containing the contents of paveledger-vercel. If you commit the entire master folder instead, set Vercel Root Directory to paveledger-vercel. Keep originals and the master ZIP out of the application repository.

## Required accounts and tools

- A Vercel account and a Git provider account, controlled by your organization.
- A dedicated Supabase project and its project URL, publishable key and server secret key.
- Node.js 22.x and npm on the development machine. The lockfile is supplied; install with npm ci.
- A real administrator email and a second person who can independently verify repairs.

## Run locally

```text
cd paveledger-vercel
npm ci
# Copy .env.example to .env.local and fill it in.
node --env-file=.env.local scripts/check-env.mjs
npm run dev
```

Windows PowerShell: use Copy-Item .env.example .env.local. macOS/Linux: use cp .env.example .env.local. Open http://localhost:3000. Never paste actual secrets into a public repository, a screenshot or a support ticket.

| Variable | Value and exposure |
| --- | --- |
| NEXT_PUBLIC_SUPABASE_URL | Project API URL; expected to be visible to the browser. |
| NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY | Browser publishable key; not the server secret. |
| SUPABASE_SECRET_KEY | Server-only secret key; never prefix with NEXT_PUBLIC_. |
| OWNER_EMAIL | Exact verified email of the initial owner. |
| WORKSPACE_ID | Stable ID, e.g. city-road-pilot. Use letters, digits, hyphen or underscore. |
| SEED_DEMO_DATA | false for an empty pilot; true for fictional examples on first initialization only. |

Budget separately for Vercel, Supabase compute/storage/egress and backups. Email, camera hardware, mobile connectivity and model inference are additional future costs. Original brochure prices are business assumptions, not hosting quotations.

# 2. Set up Supabase

## Database and storage

Create a new Supabase project. Canada Central (ca-central-1) is an available region. Select an appropriate location under your organization’s requirements. Region selection alone does not establish end-to-end Canadian data residency; review logs, support access, subprocessors, email and backups separately.

- Open the SQL Editor. Run supabase/migrations/202609250001_workspaces.sql first.
- Run supabase/migrations/202609250002_private_evidence.sql second.
- Confirm public.workspaces exists and Row Level Security is enabled. There should be no browser read/write policy for this table.
- Confirm the paveledger-evidence bucket is private, has a 3,000,000-byte limit and accepts JPEG, PNG and WebP. Do not create public storage policies.
- In a reused project, inspect all storage.objects policies: a broad existing policy may expose this bucket. A fresh dedicated project avoids that ambiguity.

## Authentication

Use email/password authentication. Disable public sign-up for the pilot. In Authentication → Users, create the owner’s account using an approved account-provisioning process and confirm that account’s email. The packaged sign-in page has no self-registration or password-reset flow; administrators handle provisioning and recovery through Supabase.

Set the production Site URL to your eventual Vercel/custom-domain URL. Add localhost only to the development project’s redirect allowlist if required. Avoid wildcard production redirect URLs. Configure your own SMTP before relying on invitation or recovery delivery.

## Verify before initializing

```text
select relrowsecurity
from pg_class
where oid = 'public.workspaces'::regclass;

select id, public, file_size_limit
from storage.buckets
where id = 'paveledger-evidence';
```

Expected results: relrowsecurity = true; bucket public = false; file_size_limit = 3000000. The workspace table is initially empty. The owner’s first authenticated request creates the row atomically.

The browser never receives the server secret. The API validates each bearer token with Supabase Auth, loads an active membership, checks role and case scope, then accesses storage with its server credential. RLS blocks direct browser table access; application authorization remains essential because the server credential has elevated access.

# 3. Deploy to Vercel and create accounts

## Vercel project settings

- Import the private Git repository. Choose the Next.js framework preset.
- Root Directory: the folder containing package.json. Install command: npm ci. Build command: npm run build. Leave Output Directory at the Next.js default.
- Select Node.js 22.x. The supplied vercel.json requests the yul1 Montréal function region and a 30-second API function duration. Confirm your plan supports the selected settings.
- Add all six environment variables. Use separate Supabase projects and keys for Preview and Production. Public variables are compiled into the client bundle, so redeploy after changing them.
- Deploy and open /api/health, /concept and /. /api/health only proves the web process responds; it does not verify database readiness.
- Sign in as OWNER_EMAIL, then confirm an empty workspace or the explicitly selected demo records.

## Bind each person to an account

For every team member, first create and confirm their Supabase Auth user. Copy that user’s UUID from Authentication → Users. In Teams & access, create a membership with that exact authentication UUID, name, email and role. Assign staff to a team and contractors to an existing contractor firm. Register the firm’s contract before adding its contractor users.

An email address alone never grants access. A valid Auth account without a bound active membership receives 403. Fictional demo personas are usable only as administrator previews unless deliberately bound to real accounts. Use genuine separate accounts for acceptance testing.

## First end-to-end case

Create a manual report with road, coordinates, accuracy, lane and description. Upload an authorized detection image. Assign a team and analyst. Have the analyst investigate and confirm it, review the matching contract, and prepare the notice. Record any external contact manually. Have the contractor acknowledge and progress the repair. A different reviewer uploads or reviews later verification evidence and closes the case.

## Production domain and handover

Add the domain in Vercel, follow the DNS values shown there, and update the Supabase Site URL. Do not infer domain availability from the historical Domain_Research.json. Give the operational owner access to hosting, database, DNS, billing and recovery accounts. Record the deployed Git commit, migration versions and responsible support contact.

# 4. Role and account management

| Role | Read scope | Allowed work |
| --- | --- | --- |
| Admin | Whole workspace | Teams, contracts, memberships, assignment and workflow; independent closure rules still apply. |
| Team lead | Their team’s cases | Assign within team, investigate, prepare notices and record progress; cannot verify closure. |
| Analyst | Cases assigned to them | Create an owned manual report, investigate, confirm, prepare notices, add evidence and record progress; cannot verify closure. |
| Reviewer | Their team’s cases | Add evidence/notes, hold/resume, independently verify closure or reopen; cannot assign or change access. |
| Contractor | Released cases for their firm | Acknowledge, start repair, claim completion, add shared repair evidence and notes. Cannot close or reopen. |
| Auditor | Whole workspace, read-only | Read cases, evidence and global audit. Cannot change workflow, upload or administer. |

Dashboards are calculated from the same filtered data returned by the server. Contractors receive only shared history and shared evidence. Their responses omit internal case notes and assigned analyst identifiers. Global audit events are limited to Admin and Auditor; membership emails and authentication IDs are limited to Admin.

## Account lifecycle

Join: create Auth user → verify identity and email → bind UUID → grant the minimum role and team → test access. Move: reassign open investigations before changing an analyst’s role or team. Leave: reassign workload, deactivate membership, then disable/revoke the Auth account and remove access to administrative services. The next API request rechecks active membership.

The app protects the current administrator and designated owner from self-demotion, suspension and rebinding. It also prevents removing the last active administrator. Add a second real administrator before relying on the system operationally. Owner recovery/transfer requires a controlled, backed-up database change by the platform administrator; it is not a self-service UI operation.

## Permission boundaries

A role preview is an administrator feature and can perform actions. The audit names the real administrator and the previewed identity. Access changes require returning to the administrator’s own identity. Pilot memberships support one role and one team; multi-team grants, SSO, MFA enforcement and time-limited vendor access require the production authorization extension.

# 5. Investigation lifecycle

| Stage | Required action or gate |
| --- | --- |
| Detected | Manual report in this release; a future camera pipeline will create candidate observations. Record location uncertainty and source. |
| Team assigned | Route to an existing responsible team. Preserve the case ID. |
| Analyst assigned | Select an active analyst in that team. An in-app assignment notification is created. |
| Investigating | Analyst examines evidence, location, road ownership, scope and duplicate candidates. Record actions in notes. |
| Confirmed | Confirm a road issue. Reject a false report or link a duplicate to its primary case. |
| Notice prepared | Select a contract on the same road that covers the case creation date; explicitly confirm location, work scope and notice terms. |
| Acknowledged | Record contractor acknowledgement. This is a workflow entry, not an email receipt. |
| Repair in progress | Track mobilization and work. No-warranty cases may progress here directly from Confirmed. |
| Awaiting verification | Record the completion claim, claimant and timestamp. The issue is still open. |
| Verified closed | An independent Admin or Reviewer accepts eligible repeat evidence and records an explicit clear-pass decision. |

## Investigation practice

Use the case history for each measured action: what was checked, what evidence supports the conclusion, who owns the next action and when follow-up is needed. Keep internal assessments internal. Before sharing, ensure the photo and note are appropriate for the contractor. The pilot does not edit or redact uploaded images.

## Priority and time targets

Urgent, Standard and Low are triage labels. The current app assigns a generic 24-hour due timestamp to new and reopened cases; it is a demonstration operational target, not a statutory response deadline. Adopt municipality-specific response policies before live use. A serious hazard requires the existing emergency/traffic-control process in parallel; warranty correspondence must not delay mitigation.

The colour-coded status label appears with text. Use status text for decisions and accessibility, never colour alone. Rejected and Duplicate are terminal classifications in the current UI; a correction requires a new linked report or a controlled administrative correction with recorded rationale.

# 6. Verification, reopening and exceptions

## Independent closure gate

The API permits Verified closed only from Awaiting verification and only for Admin or Reviewer. The real actor must differ from both the assigned analyst and the person who recorded the completion claim. Administrator preview cannot bypass this check.

The selected attachment must have purpose = verification, visibility quality = clear, reported GPS accuracy no worse than 10 metres, a capture timestamp at or after completion, and the exact same lane label. Its distance from the case point must be within max(10 m, min(25 m, case accuracy + evidence accuracy)). These are prototype tolerances; field calibration is required.

The reviewer must explicitly confirm that the same lane and defect area are visible and repaired. A missing AI detection, darkness, snow, parked vehicles, a shifted route or an obscured camera does not establish a successful repair. An uncertain pass remains open for a new pass or a site inspection.

## Reopened

From Awaiting verification or Verified closed, authorized municipal staff can reopen a failed repair with a reason. The reopened count increases, history and prior verification remain, and the case returns to investigation or repair. A new completion claim sets a new verification time boundary. Dashboards show the reopened state instead of treating the case as successfully closed.

## On hold

A hold records the preceding stage. Resume returns to exactly that stage rather than skipping work. Record why the case is blocked and who will resolve it. Contractors cannot place or resume a hold. The current app does not pause the due timer; reporting should distinguish elapsed time from any future policy-adjusted SLA clock.

## Duplicate and rejected cases

A duplicate must point to another accessible case that is neither rejected nor itself a duplicate. Its own ID, evidence and history remain. Rejection requires a reason. This version does not merge histories or delete observations. Production clustering should preserve all source observations and record every merge/split decision.

## Warranty uncertainty

A same-road/date match is only a candidate. The reviewer must check segment, lane, chainage, repair scope, exclusions, acceptance date and notice terms against the actual contract. Date matching currently uses case creation time, not an independently verified observation time. The system does not determine legal liability or send binding demands automatically.

# 7. Evidence and information architecture

| Record | Purpose and important fields |
| --- | --- |
| Workspace | Boundary: stable workspace ID, owner Auth UUID, revision, state and update time. |
| Membership | Stable member ID, bound Auth UUID, role, team/firm and active status. |
| Case | Unique PL-year-ID, point, accuracy, lane, severity, current stage, owner, deadlines and duplicate link. |
| Contract | Contract ID, firm, road, scope, warranty dates, verified contact name and email. |
| Evidence | File ID, purpose, capture/upload times, coordinates, accuracy, lane, quality, SHA-256 and sharing scope. |
| History / event | Timestamp, actor, action and reason; case history plus workspace audit list. |
| Notification | Recipient, case, message and timestamp; in-app assignment notification. |

## Photo capture today

The upload form supports selecting a photo or opening the phone camera where the browser supports capture. JPEG, PNG and WebP are accepted up to 3 MB each, with at most 40 attachments per case. HEIC, video, automatic compression, background upload and offline queues are not implemented. Convert or reduce large photos before upload.

Capture time, location, accuracy and lane are operator-entered. Timestamp checks reject future captures and captures more than 30 days before case creation. File signatures are checked and a SHA-256 hash identifies exact duplicates within a case. This is not proof of image authenticity, a malware scanner or an anti-fraud model.

## Private storage

Image bytes live in Supabase Storage, not inside the JSON workspace. Object keys use workspace/case/file IDs. By default evidence is internal; deliberately select sharing for contractor access. Contractor uploads are shared repair evidence. Authorized reads generate a URL valid for 60 seconds. A copied signed URL remains usable until its expiry; avoid including it in logs or exports.

The uploader attests that the image is authorized and redacted. There is no automatic face/plate redaction in this release. Define collection purpose, retention, access-review and deletion policies before collecting road imagery. Production should preserve protected originals, create redacted derivatives and record reviewer access in a durable evidence ledger.

# 8. Database and API design

## Implemented pilot storage

PostgreSQL public.workspaces contains one row per workspace: id text primary key; owner UUID referencing auth.users; revision integer; data JSONB; updated_at timestamptz. The JSON contains tickets, members, teams, contracts, notifications and events. This is intentionally a bounded pilot model, with a 500-case creation limit and an approximately 8-million-character state limit on ordinary mutations.

Each mutation reads the current revision, applies server-side validation, and issues one conditional UPDATE matching that revision. A competing change yields HTTP 409; the user must refresh and reconsider the change. It does not silently overwrite another user’s accepted update. Evidence uploads remove their newly written object if the subsequent metadata update fails; operators still need an orphan-object reconciliation process.

| Endpoint | Contract |
| --- | --- |
| GET /api/workspace | Bearer token; returns authorized projection and revision. Admin may supply persona for preview. |
| POST /api/workspace | JSON revision plus action: create, assign, transition, note, team, contract, member or memberUpdate. 32 KB request cap. |
| POST /api/evidence | Bearer token and multipart form with file, case, revision, metadata and authorization attestation. |
| GET /api/evidence | Case/file parameters; verifies permission and returns a 60-second signed URL. |
| GET /api/health | Public process liveness only; contains no workspace data. |

## Known architectural limits

Whole-workspace reads and writes cause contention and memory overhead as history grows. Audit history is application-managed JSON and can be changed by privileged database operators; it is not an immutable evidentiary store. The state-size guard is not a storage quota. No job queue, read replicas, transactional email outbox or unattended workflow timers are present.

## Production relational model

Before substantial fleet use, split organizations, memberships, teams, contractors, contracts, road segments, observations, cases, assignments, evidence, verification runs, case events, notices and outbox jobs into separate tables. Put organization_id on every tenant-owned row. Use composite foreign keys to prevent cross-organization references, explicit RLS policies, PostGIS segment geometry and indexed status/team/due-date queries. Keep operational state changes and an append-only event in one transaction.

# 9. Production integration design

## Device to investigation

Give every approved vehicle/device a revocable credential scoped to its municipality. Capture a client observation UUID, GPS accuracy, direction/lane, timestamp, camera calibration version and image hashes. An authenticated ingestion service validates the manifest and grants short-lived upload access. A durable queue runs quality checks, privacy filtering and versioned inference. Idempotency on organization + device + observation UUID prevents retry duplicates.

Store each observation independently. Cluster likely defects by road segment, lane, class, distance and time; uncertain clusters go to human triage. A candidate detection creates or enriches an investigation but does not establish a confirmed defect. Retain model version, confidence and human disposition so precision and false positives can be evaluated on representative routes.

## Contractor communication

Import accepted works and warranty scope from authoritative contract/GIS systems. A reviewed match selects a verified POC and permitted delivery channel. Save the approved notice and an outbox job in the same database transaction. A worker sends it using a unique idempotency key, records provider message IDs, processes signed delivery webhooks and retries transient failures with backoff. Dead-letter failures create staff follow-up. A provider delivery receipt and a contractor acknowledgement are distinct states.

## Return-pass verification

Schedule repeat coverage after the completion claim. Compare observation geometry, lane and viewing conditions; flag occlusion and uncertainty. Produce a review candidate with before/after evidence, never an automatic closure based only on non-detection. Reopened repairs return to the same case history with a new repair cycle.

## Security and operational separation

Add SSO/MFA, explicit multi-team membership grants, server rate limits, upload quarantine and decoding, signed device manifests, audit export and bounded pagination. Keep inference and slow background jobs outside request handlers. Enforce tenant scope in both API authorization and database policy. Record actor, entity, correlation ID and decision without logging credentials or unrestricted image URLs.

## Phased delivery

- Phase A: prove manual investigations, role boundaries, storage, backups and independent closure with one municipality.
- Phase B: normalize the schema and add durable events, privacy filtering, a device ingestion queue and read-only GIS/contract imports.
- Phase C: add approved notice delivery, delivery reconciliation, calibrated model evaluation and repeat-pass scheduling.
- Phase D: introduce shared tenancy and subscriptions only after isolation, recovery, load and procurement requirements pass review.

# 10. Migration, backups and operations

## Move existing data deliberately

The original Sites app uses Cloudflare D1 and ChatGPT-specific identity. The new app uses PostgreSQL and Supabase identity. Copying the SQLite schema into Supabase or pasting old owner IDs will not work. The inspected source was commit b45dacf818f1f636f300e9f160440ad5b79b37ad; the live database viewer showed one workspaces row but truncated its JSON value.

- Obtain a complete authorized D1 export or untruncated workspace JSON through the site’s database administration interface. Validate JSON and retain the original file and checksum.
- Inventory case, member, contract and history counts. Separate fictional seed records from real operations.
- Create the new Supabase accounts and an explicit old-member-ID → new-member-ID/Auth-UUID mapping. Do not migrate access by matching email alone.
- Transform ownership, assignment, actor references and any evidence keys; preserve legacy identifiers in a migration ledger. Supply required lane and evidence fields with documented uncertainty.
- Import into a separate staging deployment. Compare IDs, counts, history, attachments and role-filtered views. Do not overwrite the original site during rehearsal.
- At cutover, freeze writes, repeat export/import, reconcile counts and obtain operational sign-off. Keep the old site read-only until rollback and retention requirements are satisfied.

## Backup and restore

Use scheduled database backups appropriate to your recovery target. Supabase database backups do not contain Storage object bytes. Back up the private evidence bucket separately with its object paths and SHA-256 manifest. Protect exports as sensitive data. Back up configuration names and migration versions; keep actual credentials in your organization’s secret manager.

Restore into an isolated project first. Restore accounts/identity mappings, database state and evidence objects; then verify case counts, representative file hashes, private access and role boundaries. Set recovery objectives with the municipality. Do not promise a recovery time until this drill has been measured.

## Routine operation

Monitor API failures, 409 conflict rate, database availability, storage growth, orphan objects, open/overdue cases, ageing in Awaiting verification, reopened count and evidence upload failures. Review access regularly. Apply dependency updates in Preview with tests before promotion. Roll back application code independently of data; restoring an old database can discard accepted investigations and requires reconciliation.

# 11. Acceptance and troubleshooting

## Required live acceptance checks

- Owner initializes exactly once; an unbound or suspended account cannot open the workspace.
- Use separate real accounts for each role. Verify cross-team and cross-contractor reads and writes are denied, including direct API requests.
- Check that the publishable key cannot read public.workspaces or list/download private evidence directly.
- Complete assignment → investigation → notice → repair → independent verification. Test stale writes, rejection, duplicate linking, holds and reopening.
- Upload a real mobile photo, verify internal/shared permissions, and ensure the signed URL expires.
- Restore database plus a sample of Storage objects into a separate project. Document missing objects and recovery duration.

## Validation performed for this export

The packaged source passed dependency installation, TypeScript checking, a production Next.js build, 26 workflow/security unit tests and local API integration checks using a simulated Supabase service. These checks are recorded in VALIDATION.md. No real Supabase project, Vercel deployment, outgoing email or fleet/AI pipeline was exercised. Cloud configuration and real-account tests remain deployment acceptance work.

| Symptom | Likely cause and action |
| --- | --- |
| Sign-in fails | Check project URL/key, account password and confirmed email. An account alone is not a membership. |
| 401 / 403 | Sign in again; check exact Auth UUID, active membership, assigned team/case and contractor firm. |
| 503 storage error | Verify both SQL migrations, server key and Supabase project availability. |
| 409 on save/upload | Another change won. Refresh, review the current state and submit again. |
| Photo rejected | Use JPEG/PNG/WebP under 3 MB; check capture date, coordinates, attestation and 40-file cap. |
| Cannot close | Use an independent reviewer and qualifying later verification evidence with identical lane text. |
| Demo data persists | SEED_DEMO_DATA affects first initialization only. Use a separate workspace/project; do not delete history casually. |

This is a technically deployable pilot, not a certification of municipal production readiness. Run the live acceptance checks against your configured environment before admitting operational users.

# 12. Sources, provenance and handover

## Authoritative setup references

Vendor documentation checked on 25 September 2026. Settings and plan entitlements may change; use these pages when configuring your accounts.

- Vercel Next.js deployment: https://vercel.com/docs/frameworks/full-stack/nextjs
- Vercel regions: https://vercel.com/docs/regions
- Function region configuration: https://vercel.com/docs/functions/configuring-functions/region
- Supabase Next.js quickstart: https://supabase.com/docs/guides/getting-started/quickstarts/nextjs
- Supabase regions: https://supabase.com/docs/guides/platform/regions
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase Auth getUser: https://supabase.com/docs/reference/javascript/auth-getuser
- Private Storage access: https://supabase.com/docs/guides/storage/security/access-control
- Database backups and Storage exclusion: https://supabase.com/docs/guides/platform/backups

## Recovered project material

Thirteen accessible PaveLedger file artifacts and the saved site source were identified. Original documents include the business plan, government brochure, fleet/contractor brochure and engineering design in Word/PDF; financial workbook; logo; overview image; complete-package ZIP; and earlier damaged Vercel ZIP. The complete-package ZIP also supplied historical domain research and its original start guide.

The saved site source was archived unchanged at commit b45dacf818f1f636f300e9f160440ad5b79b37ad. The new deployable project builds on the recovered Vercel conversion, restores missing source assets, and adds the access, evidence and investigation controls described here. Originals are historical references; this guide and current source describe version 2.0 behaviour.

## Handover record to complete

| Item | Record before launch |
| --- | --- |
| Operational owner | Named municipality owner and independent reviewer. |
| Technical owner | Hosting, database, DNS, monitoring and incident contacts. |
| Deployment | Repository, production URL, deployed commit and environment IDs. |
| Recovery | Backup location, last restore drill, recovery objectives and escalation path. |
| Acceptance | Role checks, workflow sign-off, data reconciliation and remaining integrations. |

No live-site settings were changed as part of this export. There is no automatic migration of its data, accounts or existing sessions. The complete master package preserves accessible project materials without claiming access to every historical ChatGPT conversation.
