import pathlib, re
from datetime import date

VERSION = "2.8.0"
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

A = 'lib/actions.ts'

replace_once(A,
    "event='Contract updated: '+existing.id;\n }else if(action==='team'){",
    """event='Contract updated: '+existing.id;
 }else if(action==='bulkImportContracts'){
  if(!isActive(m)||!roleCan(s,m.role,'contracts'))throw new AppError('This action is not permitted for your role.',403);
  const items=Array.isArray(body.items)?body.items:[];
  if(!items.length)throw new AppError('No contracts to import.');
  if(items.length>200)throw new AppError('Import up to 200 contracts at a time.');
  const importSchema=z.object({contractor:short,road:short,scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||''),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||'')});
  let created=0,skipped=0;
  for(const raw of items){
   const parsed=importSchema.safeParse(raw);
   if(!parsed.success){skipped++;continue}
   const iv=parsed.data;
   if(iv.end<iv.start){skipped++;continue}
   const id='CT-'+crypto.randomUUID().slice(0,8).toUpperCase();
   s.contracts.push({...iv,id});
   created++;
  }
  event='Bulk imported '+created+' contract(s)'+(skipped?', skipped '+skipped+' invalid row(s)':'');
 }else if(action==='team'){""",
    "actions.ts: add bulkImportContracts action")

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
- Added bulkImportContracts action: validates each row with the same rules as a single contract, skips invalid rows rather than failing the whole batch, capped at 200 per import
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
