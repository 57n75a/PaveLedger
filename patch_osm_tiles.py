#!/usr/bin/env python3
"""Fix the OpenStreetMap tile 'Blocked' error.
Cause: next.config.ts sends 'Referrer-Policy: same-origin', so the browser sends no Referer
header to tile.openstreetmap.org, which its tile usage policy requires.
Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, datetime

CFG = 'next.config.ts'
MAP = 'components/scope-locator.tsx'
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

cfg = read(CFG)
cfg = swap(cfg,
  "{key:'Referrer-Policy',value:'same-origin'}",
  "{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'}",
  'referrer policy')

m = read(MAP)
m = swap(m,
  "{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}",
  "{maxZoom:19,attribution:'&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors',referrerPolicy:'strict-origin-when-cross-origin'}",
  'tile layer options')

v = read(VERSION)
found = re.findall(r'\d+\.\d+\.\d+', v)
if len(found) != 1:
    die(f'{VERSION}: expected exactly one x.y.z, found {found}')
old_v = found[0]
maj, mnr, pat = map(int, old_v.split('.'))
new_v = f'{maj}.{mnr}.{pat + 1}'
v = v.replace(old_v, new_v)

c = read(CHANGELOG)
h = re.search(r'^## .*$', c, re.M)
if not h:
    die(f'{CHANGELOG}: no "## " heading found to insert before')
print('Top existing changelog heading:', h.group(0))
entry = (f'## {new_v} - {datetime.date.today().isoformat()}\n'
         '- Fix: map tiles were blocked by OpenStreetMap because no Referer header was sent. Referrer-Policy is now strict-origin-when-cross-origin (only the site origin is sent to other sites).\n'
         '- Map attribution now links to the OpenStreetMap copyright page, as the tile policy requires.\n\n')
c = c[:h.start()] + entry + c[h.start():]

open(CFG, 'w', encoding='utf-8').write(cfg)
open(MAP, 'w', encoding='utf-8').write(m)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v}. Now run: npm run build')
