#!/usr/bin/env python3
"""Move 'Edit branding' out of the sidebar into the Admin-only account menu.
Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, datetime

WS = 'app/workspace.tsx'
VERSION = 'lib/version.ts'
CHANGELOG = 'CHANGELOG.md'

def die(msg):
    print('ABORT: ' + msg); sys.exit(1)

def read(p):
    try:
        return open(p, encoding='utf-8').read()
    except FileNotFoundError:
        die(p + ' not found (run from repo root)')

def swap(src, old, new, label):
    n = src.count(old)
    if n != 1:
        die(f'{label}: anchor found {n} times (expected 1)')
    return src.replace(old, new)

w = read(WS)

# 1. remove the sidebar button (the logo and slogan display stay as they are)
w = swap(w,
  """{role==='Admin'&&<><br/><button className="text-button" onClick={()=>setBrandingOpen(true)}>Edit branding</button></>}""",
  "",
  'sidebar branding button')

# 2. add an Admin-only entry to the account dropdown, right after "Edit profile"
w = swap(w,
  """<DropdownMenuItem onClick={()=>setProfileOpen(true)}>Edit profile</DropdownMenuItem>""",
  """<DropdownMenuItem onClick={()=>setProfileOpen(true)}>Edit profile</DropdownMenuItem>{role==='Admin'&&<DropdownMenuItem onClick={()=>setBrandingOpen(true)}>Platform settings: branding</DropdownMenuItem>}""",
  'account menu entry')

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
         '- Branding editor moved from the sidebar to the account menu (Platform settings: branding), shown to Admin only. The logo and slogan still display for everyone.\n\n')
c = c[:m.start()] + entry + c[m.start():]

open(WS, 'w', encoding='utf-8').write(w)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v}. Now run: npm run build')
