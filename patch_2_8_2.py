#!/usr/bin/env python3
"""PaveLedger 2.8.1 -> 2.8.2 patch. Run from the repo root.
All checks happen before anything is written; if any anchor text is not
found exactly once, the script aborts and changes nothing."""
import re, sys, datetime

ACTIONS = 'lib/actions.ts'
VERSION = 'lib/version.ts'
CHANGELOG = 'CHANGELOG.md'

def die(msg):
    print('ABORT: ' + msg); sys.exit(1)

def read(p):
    try:
        return open(p, encoding='utf-8').read()
    except FileNotFoundError:
        die(p + ' not found (run from repo root)')

a = read(ACTIONS)

def swap(src, old, new, label):
    n = src.count(old)
    if n != 1:
        die(f'{label}: anchor found {n} times (expected 1)')
    return src.replace(old, new)

# 1. Non-admins must not modify an existing Vehicle account
a = swap(a,
  "if(m.role!=='Admin'&&existing?.role==='Admin')throw new AppError('Only an administrator can modify Administrator access.',403);",
  "if(m.role!=='Admin'&&existing?.role==='Admin')throw new AppError('Only an administrator can modify Administrator access.',403);"
  "if(m.role!=='Admin'&&existing?.role==='Vehicle')throw new AppError('Only an administrator can create or modify Vehicle accounts.',403);",
  'vehicle-modify')

# 2a. size guard helper, defined right after `let event=action;`
a = swap(a,
  "let event=action;",
  "let event=action;const sizeGuard=()=>{if(JSON.stringify(s).length>8_000_000)throw new AppError('Pilot workspace size limit reached. Export and migrate to the normalized production model.')};",
  'size-guard helper')

# 2b. rolePermissions: write the audit event before the early return
a = swap(a,
  "s.rolePermissions=clean;event='Role permissions updated';return}",
  "s.rolePermissions=clean;event='Role permissions updated';s.events.unshift({at:now,actor,action:event});return}",
  'rolePermissions audit')

# 2c. branding: audit + size guard
a = swap(a,
  "event='Branding updated';return}",
  "event='Branding updated';s.events.unshift({at:now,actor,action:event});sizeGuard();return}",
  'branding audit')

# 2d. selfProfile: size guard (photo up to 700 KB)
a = swap(a,
  "action:'Profile name updated: '+name});return}",
  "action:'Profile name updated: '+name});sizeGuard();return}",
  'selfProfile guard')

# version + changelog
v = read(VERSION)
found = re.findall(r'\d+\.\d+\.\d+', v)
if len(found) != 1:
    die(f'{VERSION}: expected exactly one x.y.z, found {found}')
old_v = found[0]
maj, mnr, pat = map(int, old_v.split('.'))
new_v = f'{maj}.{mnr}.{pat + 1}'
v = v.replace(old_v, new_v)

c = read(CHANGELOG)
m = re.search(r'^## .*$', c, re.M)
if not m:
    die(f'{CHANGELOG}: no "## " heading found to insert before')
print('Top existing changelog heading:', m.group(0))
entry = (f'## {new_v} - {datetime.date.today().isoformat()}\n'
         '- Security: only an Admin can modify an existing Vehicle account (previously a Team lead or Director could change or deactivate one by submitting a different role).\n'
         '- Audit: role-permission and branding changes are now written to the event log.\n'
         '- Safety: branding and profile-photo updates now respect the 8 MB workspace size limit.\n\n')
c = c[:m.start()] + entry + c[m.start():]

open(ACTIONS, 'w', encoding='utf-8').write(a)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v}. Now run: npm run build')
