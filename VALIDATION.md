# Validation record — PaveLedger v2.0

Export date: 25 September 2026. Target platform: Next.js on Vercel, Node.js 22.x, Supabase Auth/PostgreSQL/private Storage.

| Check | Result and scope |
| --- | --- |
| Dependency installation | npm ci completed using the supplied lockfile. |
| TypeScript | next typegen and tsc --noEmit passed. |
| Production compilation | Next.js production build passed on Node 22.23.3 and Node 24.19.0. |
| Workflow unit tests | 26 passed; role scope, assignment, contract gates, hold/resume, duplicate links, independent closure, reopening and account protection. |
| Local API integration | 22 assertions passed against the built app with simulated Supabase HTTP endpoints. |
| Documents | All 13 final guide pages rendered and visually inspected. |
| Archives | ZIP entries checked with CRC verification; SHA-256 manifests supplied. |

The integration checks exercise public page responses, missing/invalid/unbound authentication, filtered analyst/contractor data, hidden internal notes, no-store headers, foreign-origin rejection, revision conflicts, accepted mutations, evidence upload and evidence access controls. The local fixture is explicitly synthetic. No external messages are sent.

Not verified here: actual Supabase SQL execution/RLS and Storage permissions, real Auth provisioning, real mobile-camera/browser interaction, Vercel cloud deployment or plan entitlements, production load, penetration testing, full live-data migration, database/object restore, email delivery or AI/fleet ingestion. Perform the live acceptance checklist in the guide before operational use.

The earlier damaged reference ZIP is intentionally preserved inside the master archive and remains damaged; the newly created outer archives and deployable project ZIP pass integrity checks.

## Reproduce

```sh
npm ci
npm run typecheck
npm test
npm run build
npm run test:integration
```

The API test starts local services and uses port 4319. If your shell routes local requests through an HTTP proxy, add localhost and 127.0.0.1 to NO_PROXY or disable that proxy for the test. It does not require real Supabase credentials. Build before running the integration script.
