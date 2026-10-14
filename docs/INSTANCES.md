# Country instances (Serbia and Canada)

One codebase runs as separate deployments. Each deployment picks a country profile with one setting; everything that differs between countries lives in `lib/instance.ts`.

| | Serbia | Canada |
|---|---|---|
| `NEXT_PUBLIC_INSTANCE` | `rs` (default when unset) | `ca` |
| Brand and logo | PaveLedger Srbija, `/logo.png` | PaveLedger Canada, `/logo-ca.svg` |
| Languages (default first) | Serbian (Latin), English | English, French |
| Dates, currency | sr-Latn-RS, RSD | en-CA / fr-CA, CAD |
| Address search | Serbia only | Canada only |
| Demo pack | `demo/serbia.json` (Užice, Beograd) | `demo/canada.json` (Waterloo Region) |
| Concept page pricing | On request | CAD planning prices |

## Demo setup: two Vercel projects, one Supabase project

Both demos can share one Supabase project. Each deployment uses its own `WORKSPACE_ID`, and photos and documents are stored under that ID, so the data never mixes. Sign-in accounts are shared; a person only gets into a demo where they are a member.

| Variable | Serbia project | Canada project |
|---|---|---|
| `NEXT_PUBLIC_INSTANCE` | `rs` | `ca` |
| `WORKSPACE_ID` | keep the current value | `demo-ca` |
| `OWNER_EMAIL` | your email | your email (or another owner) |
| `SEED_DEMO_DATA` | `true` for a demo | `true` |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` | same values | same values |
| `CRON_SECRET` | any long random string | its own long random string |
| `RESEND_API_KEY`, `MAIL_FROM`, `SUPPORT_EMAIL` | optional | optional |

### Create the Canada demo

1. Vercel → Add New → Project → import the `PaveLedger` GitHub repository. Name it `paveledger-ca`; it will be served at `paveledger-ca.vercel.app`.
2. Before the first deploy, add the variables from the Canada column. Copy the three Supabase values from the Serbian project (Settings → Environment Variables).
3. Deploy. Sign in with `OWNER_EMAIL`; the workspace is created with the Canada demo pack.
4. Optional: in the Serbian project, Settings → Domains, add `paveledger-rs.vercel.app` (if available). `paveledger.vercel.app` keeps working.

Both projects deploy from `main`, so one push updates both demos.

## Demo data

- Admins reload a pack from User Profile → Platform settings → Demo data. It replaces tickets, contracts, teams and demo people; real sign-in accounts are kept.
- Packs are JSON files in `demo/`. Dates are given as `daysAgo`, so a freshly loaded demo always looks current. `path` lists the stages a ticket has gone through after Detected; the loader rejects paths the workflow does not allow (`npm test` checks both packs).
- Demo people cannot sign in. Use Preview role at the top of the workspace to see it as any of them.

## Keeping the database awake

The free Supabase tier pauses a project after about a week without activity. `vercel.json` runs `/api/keepalive` every 5 days (and `/api/auto-close` daily), each a small read. Both need `CRON_SECRET` set in the project.

## Address search

The new-ticket form suggests addresses as you type, limited to the instance's country (Photon, based on OpenStreetMap). "Find address on map" still uses Nominatim. Nothing is stored. For a client, the official registers (RGZ adresni registar for Serbia, Statistics Canada's Open Database of Addresses for Canada) can be loaded into a dedicated table later; Canada needs a paid database for the full set.

## Moving a demo to production

Give the instance its own Supabase project (in Canada for Canadian clients), set the same variables, and attach the client's domain. No code changes are needed.
