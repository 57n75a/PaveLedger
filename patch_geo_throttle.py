#!/usr/bin/env python3
"""Add a 1-request-per-second throttle to Nominatim lookups in lib/geo.ts
(OpenStreetMap's usage policy allows at most 1 request per second).
Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, datetime

GEO = 'lib/geo.ts'
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

g = read(GEO)
sig = "async function nominatim(path:string,params:URLSearchParams,timeoutMs:number){"
g = swap(g, sig,
  "let nextSlot=0;\n"
  "const sleep=(ms:number)=>new Promise<void>(r=>setTimeout(r,ms));\n"
  "// Nominatim policy: at most 1 request per second. Space requests out on this server instance;\n"
  "// if the queue is already more than 8 seconds long, give up so callers fall back instead of hanging.\n"
  "async function gate(){const now=Date.now();const start=Math.max(now,nextSlot);if(start-now>8000)throw new Error('busy');nextSlot=start+1100;if(start>now)await sleep(start-now)}\n"
  "\n" + sig + "await gate();",
  'nominatim gate')

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
         '- Street and address lookups are now spaced at least 1.1 seconds apart per server instance, to follow the OpenStreetMap Nominatim usage policy.\n\n')
c = c[:h.start()] + entry + c[h.start():]

open(GEO, 'w', encoding='utf-8').write(g)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v}. Now run: npm run build')
