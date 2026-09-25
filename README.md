# PaveLedger for Vercel — v2.0

A municipal road-investigation pilot using Next.js, Supabase Auth, PostgreSQL and private Storage.

## Start here

1. Follow [DEPLOYMENT.md](DEPLOYMENT.md) and apply both SQL migrations to a dedicated Supabase project.
2. Copy `.env.example` to `.env.local` and supply your project settings.
3. Run `npm ci`, then `node --env-file=.env.local scripts/check-env.mjs`, then `npm run dev`.
4. Sign in with the confirmed account matching `OWNER_EMAIL`. Provision real users in Supabase and bind their exact UUIDs in Teams & access.
5. Import this folder into Vercel with the Next.js preset and Node.js 22.x.

## Included

- Server-enforced roles: Admin, Team lead, Analyst, Reviewer, Contractor and Auditor.
- Assignment notifications, investigation stages, warranty-scope review and prepared notices.
- Private photo upload, internal/shared evidence and short-lived authorized downloads.
- Independent closure checks, duplicate links, holds, reopening and case/audit history.
- Colour-coded, role-filtered dashboards and a public concept page at `/concept`.

## Pilot scope

One workspace per deployment. The operational state is a bounded JSONB record: 500 cases; ordinary mutations enforce an approximately 8-million-character limit. Photos are separate private objects, at most 40 per case and 3 MB each. Read the architecture guide before increasing these limits or introducing shared tenancy.

Live cameras, AI inference, automatic email, durable reminders, geographic contract matching, native/offline mobile capture and billing are not implemented. Photo metadata is manually entered. `Notice prepared` does not send an email. A missing AI detection never proves repair completion.

`SEED_DEMO_DATA=true` creates fictional examples on first initialization only. Keep it false for real operations. Administrator persona preview can mutate data and is recorded with the real actor; it is not an authorization bypass for ordinary members.

## Validation

```sh
npm run typecheck
npm test
npm run build
npm run test:integration
```

Integration tests use a local in-memory Supabase HTTP double. They do not validate a real cloud database or its policies. See [VALIDATION.md](VALIDATION.md) and perform the documented live acceptance checks after deployment.

## Documentation

- [Full deployment, operations and architecture guide](docs/OPERATIONS_AND_ARCHITECTURE.md)
- [API contract](docs/API.md)
- [Architecture and investigation diagrams](docs/DIAGRAMS.md)
- [Source provenance](SOURCE_PROVENANCE.md)

The existing Sites application and its database were not modified. Live data and old sign-in identities are not automatically migrated.
