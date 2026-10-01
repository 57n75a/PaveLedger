import pathlib, re, subprocess, sys
from datetime import date

VERSION = "2.5.0"
TODAY = date.today().isoformat()

def replace_once(path, old, new, label):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        print(f"SKIP ({count} matches, expected 1): {label} in {path}")
        return False
    p.write_text(text.replace(old, new, 1))
    print(f"OK: {label}")
    return True

print("== Installing jspdf + jspdf-autotable (client-side PDF generation, no server needed) ==")
rc = subprocess.run(['npm', 'install', 'jspdf@2.5.2', 'jspdf-autotable@3.8.4']).returncode
if rc != 0:
    print(f"ERROR: npm install failed (exit {rc}). No source files were changed.")
    sys.exit(1)

WP = 'app/workspace.tsx'

replace_once(WP,
    "import {APP_VERSION} from '@/lib/version';",
    "import {APP_VERSION} from '@/lib/version';\nimport jsPDF from 'jspdf';\nimport autoTable from 'jspdf-autotable';",
    "workspace.tsx: import jsPDF")

replace_once(WP,
    "function exportCSV(){const rows=[['Ticket','Road','Status','Priority','Team','Latitude','Longitude','Reopens'],...filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.lat,t.lng,t.reopened])];download('PaveLedger_Investigations.csv',rows.map(r=>r.map(x=>'\"'+String(x).replace(/^[=+@-]/,\"'$&\").replaceAll('\"','\"\"')+'\"').join(',')).join('\\n'),'text/csv')}",
    "function exportCSV(){const rows=[['Ticket','Road','Status','Priority','Team','Latitude','Longitude','Reopens'],...filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.lat,t.lng,t.reopened])];download('PaveLedger_Tickets.csv',rows.map(r=>r.map(x=>'\"'+String(x).replace(/^[=+@-]/,\"'$&\").replaceAll('\"','\"\"')+'\"').join(',')).join('\\n'),'text/csv')}\nfunction exportPDF(){const doc=new jsPDF();doc.setFontSize(14);doc.text('PaveLedger Tickets Export',14,15);doc.setFontSize(9);doc.text(new Date().toLocaleString(),14,21);autoTable(doc,{startY:26,head:[['Ticket','Road','Status','Priority','Team','Contractor','Observations']],body:filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.contractor||'Unassigned',String(t.observations)]),styles:{fontSize:8}});doc.save('PaveLedger_Tickets.pdf')}",
    "workspace.tsx: add exportPDF function, fix CSV filename")

replace_once(WP,
    '<button className="secondary" onClick={exportCSV}><Download size={17}/>Export</button>',
    '<button className="secondary" onClick={exportCSV}><Download size={17}/>Export CSV</button><button className="secondary" onClick={exportPDF}><Download size={17}/>Export PDF</button>',
    "workspace.tsx: add Export PDF button next to Export CSV")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")
pkg = pathlib.Path('package.json')
new_pkg, n = re.subn(r'"version":\s*"[^"]*"', f'"version": "{VERSION}"', pkg.read_text(), count=1)
if n == 1:
    pkg.write_text(new_pkg)
    print(f"OK: package.json version set to {VERSION}")
changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added PDF export alongside CSV export on the Tickets dashboard (client-side, no server cost)
- Fixed the CSV export filename (was still PaveLedger_Investigations.csv)
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
