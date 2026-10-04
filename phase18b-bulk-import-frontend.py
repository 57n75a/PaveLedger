import pathlib, re, subprocess, sys
from datetime import date

VERSION = "2.8.1"
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

print("== Installing xlsx (SheetJS) for XLSX/CSV parsing, no server needed ==")
rc = subprocess.run(['npm', 'install', 'xlsx@0.18.5']).returncode
if rc != 0:
    print(f"ERROR: npm install failed (exit {rc}). No source files were changed.")
    sys.exit(1)

# ---------- 1. New component: components/contract-import.tsx ----------
component_code = r"""'use client';
import {useState} from 'react';
import * as XLSX from 'xlsx';
import {toast} from 'sonner';

const FIELDS=[
 {key:'contractor',label:'Contractor firm',required:true},
 {key:'road',label:'Road name',required:true},
 {key:'start',label:'Warranty begins (YYYY-MM-DD)',required:true},
 {key:'end',label:'Warranty ends (YYYY-MM-DD)',required:true},
 {key:'poc',label:'Point of contact',required:true},
 {key:'email',label:'Contact email',required:true},
 {key:'phone',label:'Phone number',required:false},
 {key:'scope',label:'Work scope',required:false},
 {key:'address',label:'Address',required:false},
];

export default function ContractImport({mutate,busy,onDone}:{mutate:(b:any)=>Promise<boolean>,busy:boolean,onDone:()=>void}){
 const [rows,setRows]=useState<Record<string,any>[]>([]);
 const [columns,setColumns]=useState<string[]>([]);
 const [mapping,setMapping]=useState<Record<string,string>>({});
 const [selected,setSelected]=useState<Set<number>>(new Set());
 const [fileKind,setFileKind]=useState<'table'|'xml'|'pdf'|null>(null);

 function autoMap(cols:string[]){
  const guess:Record<string,string>={};
  const norm=(s:string)=>s.toLowerCase().replace(/[^a-z]/g,'');
  for(const f of FIELDS){
   const hit=cols.find(c=>norm(c).includes(norm(f.key))
    ||(f.key==='contractor'&&norm(c).includes('company'))
    ||(f.key==='road'&&(norm(c).includes('street')||norm(c).includes('location')))
    ||(f.key==='poc'&&norm(c).includes('contact'))
    ||(f.key==='start'&&(norm(c).includes('begin')||norm(c).includes('from')))
    ||(f.key==='end'&&(norm(c).includes('expir')||norm(c).includes('to'))));
   if(hit)guess[f.key]=hit;
  }
  setMapping(guess);
 }

 async function handleFile(file:File){
  const name=file.name.toLowerCase();
  if(name.endsWith('.pdf')){setFileKind('pdf');setRows([]);setColumns([]);return}
  if(name.endsWith('.xml')){
   const text=await file.text();
   const doc=new DOMParser().parseFromString(text,'application/xml');
   if(doc.querySelector('parsererror')){toast.error('Could not parse this XML file');return}
   const counts=new Map<string,number>();
   doc.querySelectorAll('*').forEach(el=>{counts.set(el.tagName,(counts.get(el.tagName)||0)+1)});
   let recordTag='',max=1;
   counts.forEach((c,tag)=>{if(c>max){max=c;recordTag=tag}});
   if(!recordTag){toast.error('Could not find repeated records in this XML file');return}
   const records=Array.from(doc.getElementsByTagName(recordTag));
   const extracted=records.map(rec=>{const obj:Record<string,any>={};Array.from(rec.children).forEach(child=>{obj[child.tagName]=child.textContent||''});return obj});
   const cols=Array.from(new Set(extracted.flatMap(r=>Object.keys(r))));
   setColumns(cols);setRows(extracted);setFileKind('xml');setSelected(new Set(extracted.map((_,i)=>i)));autoMap(cols);
   return;
  }
  const buf=await file.arrayBuffer();
  const wb=XLSX.read(buf,{type:'array'});
  const sheet=wb.Sheets[wb.SheetNames[0]];
  const json:Record<string,any>[]=XLSX.utils.sheet_to_json(sheet,{defval:''});
  if(!json.length){toast.error('No rows found in this file');return}
  const cols=Array.from(new Set(json.flatMap(r=>Object.keys(r))));
  setColumns(cols);setRows(json);setFileKind('table');setSelected(new Set(json.map((_,i)=>i)));autoMap(cols);
 }

 function buildItems(){
  return rows.filter((_,i)=>selected.has(i)).map(r=>{
   const item:Record<string,string>={};
   for(const f of FIELDS)item[f.key]=mapping[f.key]?String(r[mapping[f.key]]??'').trim():'';
   return item;
  });
 }

 async function doImport(){
  const items=buildItems();
  const missing=items.some(it=>FIELDS.some(f=>f.required&&!it[f.key]));
  if(missing){toast.error('One or more selected rows are missing a required field (contractor, road, dates, point of contact, or email). Fix the mapping or deselect those rows.');return}
  if(await mutate({action:'bulkImportContracts',items}))onDone();
 }

 return <div className="form">
  <label>Source file (XLSX, XLS, CSV, or XML)<input type="file" accept=".xlsx,.xls,.csv,.xml" onChange={e=>{const f=e.target.files?.[0];if(f)handleFile(f)}}/></label>
  {fileKind==='pdf'&&<p className="footnote">PDF structured import isn't supported \u2014 PDF layouts vary too much to map reliably. Convert the file to XLSX or CSV first, or enter these contracts manually.</p>}
  {rows.length>0&&<>
   <h3>Map columns</h3>
   {FIELDS.map(f=><label key={f.key}>{f.label}{f.required?' *':''}<select value={mapping[f.key]||''} onChange={e=>setMapping({...mapping,[f.key]:e.target.value})}><option value="">-- not mapped --</option>{columns.map(c=><option key={c} value={c}>{c}</option>)}</select></label>)}
   <h3>Preview ({selected.size} of {rows.length} selected)</h3>
   <div style={{maxHeight:240,overflowY:'auto',border:'1px solid #e5e7eb',borderRadius:8}}>
    {rows.map((r,i)=><label key={i} className="check" style={{display:'flex',gap:8,padding:'6px 10px',borderBottom:'1px solid #f0f1f3'}}>
      <input type="checkbox" checked={selected.has(i)} onChange={e=>{const s=new Set(selected);if(e.target.checked)s.add(i);else s.delete(i);setSelected(s)}}/>
      <span>{mapping.contractor?String(r[mapping.contractor]):'(contractor not mapped)'} \u2014 {mapping.road?String(r[mapping.road]):'(road not mapped)'}</span>
    </label>)}
   </div>
   <button className="primary" disabled={busy||!selected.size} onClick={doImport}>Import {selected.size} contract{selected.size===1?'':'s'}</button>
  </>}
 </div>;
}
"""
cp = pathlib.Path('components/contract-import.tsx')
if cp.exists():
    print(f"SKIP: {cp} already exists")
else:
    cp.write_text(component_code, encoding='utf-8')
    print(f"OK: created {cp}")

# ---------- 2. Wire into workspace.tsx ----------
WP = 'app/workspace.tsx'

replace_once(WP,
    "import {APP_VERSION} from '@/lib/version';",
    "import {APP_VERSION} from '@/lib/version';\nimport ContractImport from '@/components/contract-import';",
    "workspace.tsx: import ContractImport")

replace_once(WP,
    "[theme,setTheme]=useState<'light'|'dark'>('light'),[brandingOpen,setBrandingOpen]=useState(false);",
    "[theme,setTheme]=useState<'light'|'dark'>('light'),[brandingOpen,setBrandingOpen]=useState(false),[importOpen,setImportOpen]=useState(false);",
    "workspace.tsx: add importOpen state")

replace_once(WP,
    '''{role==='Admin'&&<button className="primary" onClick={()=>setContractOpen(true)}>Register contract</button>}''',
    '''{role==='Admin'&&<><button className="primary" onClick={()=>setContractOpen(true)}>Register contract</button><button className="secondary" onClick={()=>setImportOpen(true)}>Import contracts</button></>}''',
    "workspace.tsx: add Import contracts button")

replace_once(WP,
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={importOpen} onOpenChange={setImportOpen}><DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}><DialogHeader><DialogTitle>Import contracts</DialogTitle><DialogDescription>Upload a spreadsheet or XML export, map its columns, review, then import.</DialogDescription></DialogHeader><ContractImport mutate={mutate} busy={busy} onDone={()=>setImportOpen(false)}/></DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add Import contracts dialog")

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
- Added "Import contracts" (Admin): upload XLSX/XLS/CSV or XML, map columns to contract fields (auto-guessed), review and select rows, then import. PDF shows a message suggesting conversion to CSV first, since reliable automatic PDF table extraction isn't realistic across arbitrary government formats.
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
