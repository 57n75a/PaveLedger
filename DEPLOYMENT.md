# Deployment checklist

The complete instructions, role model and recovery runbook are in [docs/OPERATIONS_AND_ARCHITECTURE.md](docs/OPERATIONS_AND_ARCHITECTURE.md).

## Supabase

1. Create a dedicated project. Choose a suitable region; Canada Central is available. Review your data-location requirements separately.
2. Run `supabase/migrations/202609250001_workspaces.sql`, then `202609250002_private_evidence.sql` in SQL Editor.
3. Confirm RLS on `public.workspaces` and a private `paveledger-evidence` bucket. Do not grant direct browser access.
4. Disable public sign-up. Create and confirm the designated owner account in Authentication → Users.
5. Obtain the project URL, publishable key and server-only secret key.

## Local setup

Install Node.js 22.x. In this folder:

```sh
npm ci
# Copy .env.example to .env.local and edit it.
node --env-file=.env.local scripts/check-env.mjs
npm run dev
```

Use `cp .env.example .env.local` on macOS/Linux or `Copy-Item .env.example .env.local` in PowerShell. Never commit `.env.local`.

## Vercel

Import this folder through your private Git repository. Framework: Next.js. Node: 22.x. Install: `npm ci`. Build: `npm run build`. Output: default. Set the Root Directory to the directory containing this package.json, not the master archive root.

Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `OWNER_EMAIL`, `WORKSPACE_ID` and `SEED_DEMO_DATA=false` in the Vercel environment. Use a separate database for previews. Public variables require a new build after changes.

The included vercel.json requests Montréal (`yul1`) and 30-second Node API functions. Verify your plan supports the settings. No actual Vercel deployment has been performed for this export.

Open the deployed `/api/health` and `/`. Sign in as the owner to initialize the database row. Then create confirmed Auth accounts for other staff and bind their exact UUIDs in Teams & access. Register a contractor contract before adding contractor membership.

Configure the Supabase Site URL and approved redirects for your final HTTPS domain. Provision SMTP if using invitation/recovery messages. The app itself does not send contractor messages.

## Before operational use

Run separate-account role checks, a complete repair/reopen cycle, private-file tests and a database-plus-Storage restore drill. The health endpoint is process liveness only. Source ZIPs do not contain live database contents. Migration from D1/ChatGPT identity needs a complete export and explicit account mapping.
