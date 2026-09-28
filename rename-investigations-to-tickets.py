import pathlib, re
from datetime import date

VERSION = "2.2.1"
TODAY = date.today().isoformat()

# Order matters: article rules first so we never produce "an ticket".
RULES = [
    ("an investigation", "a ticket"),
    ("An investigation", "A ticket"),
    ("AN INVESTIGATION", "A TICKET"),
    ("Investigations", "Tickets"),
    ("investigations", "tickets"),
    ("INVESTIGATIONS", "TICKETS"),
    ("Investigation", "Ticket"),
    ("investigation", "ticket"),
    ("INVESTIGATION", "TICKET"),
]

files = sorted(set(list(pathlib.Path('app').rglob('*.ts*')) + list(pathlib.Path('lib').rglob('*.ts'))))
finder = re.compile(r'investigation', re.IGNORECASE)

total = 0
for p in files:
    original = p.read_text()
    matches = list(finder.finditer(original))
    if not matches:
        continue
    print(f"\n{p}: {len(matches)} occurrence(s)")
    for m in matches:
        a, b = max(0, m.start() - 35), min(len(original), m.end() + 35)
        snippet = original[a:b].replace("\n", " ")
        print(f"    ...{snippet}...")
    updated = original
    for old, new in RULES:
        updated = updated.replace(old, new)
    if updated != original:
        p.write_text(updated)
        total += len(matches)
        print(f"  -> renamed in {p}")

if total == 0:
    print("\nNothing to rename (already done, or no matches found).")
else:
    print(f"\nRenamed {total} occurrence(s) in total.")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

pkg = pathlib.Path('package.json')
pkg_text = pkg.read_text()
new_pkg, n = re.subn(r'"version":\s*"[^"]*"', f'"version": "{VERSION}"', pkg_text, count=1)
if n == 1:
    pkg.write_text(new_pkg)
    print(f"OK: package.json version set to {VERSION}")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Renamed "Investigations" to "Tickets" everywhere users see it: sidebar, page titles, buttons, dialogs, filters, search, exports, and messages
- Internal code names (types, variables, API fields) are unchanged
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
