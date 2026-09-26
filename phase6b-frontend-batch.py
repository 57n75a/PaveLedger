import pathlib
from datetime import date

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

VERSION = "2.0.8"
TODAY = date.today().isoformat()

ARCHIVE_BLOCK = '''<div className="button-row">{t.archived?<><span className="muted">Archived</span>{['Admin','Team lead','Director'].includes(data.viewer.role)&&<button className="secondary" disabled={busy} onClick={()=>mutate({action:'unarchive',id:t.id})}>Unarchive</button>}</>:<>{['Admin','Team lead','Director'].includes(data.viewer.role)&&<button className="secondary" disabled={busy} onClick={()=>mutate({action:'archive',id:t.id})}>Archive case</button>}{['Analyst','Head Analyst'].includes(data.viewer.role)&&(t.archiveRequested?<span className="muted">Archive requested</span>:<button className="secondary" disabled={busy} onClick={()=>mutate({action:'requestArchive',id:t.id})}>Request archive</button>)}</>}</div>'''

# ---------- 1. Remove archive block from its current spot (right after the note) ----------
replace_once('app/workspace.tsx',
    '<p className="footnote">{t.note}</p>' + ARCHIVE_BLOCK,
    '<p className="footnote">{t.note}</p>',
    "workspace.tsx: remove archive controls from top-of-tab location")

# ---------- 2. Re-insert archive block at the bottom of the investigate tab ----------
replace_once('app/workspace.tsx',
    '<p className="footnote">Draft download only. Email delivery is not connected.</p></TabsContent>',
    '<p className="footnote">Draft download only. Email delivery is not connected.</p>' + ARCHIVE_BLOCK + '</TabsContent>',
    "workspace.tsx: move archive controls to bottom of investigate tab")

# ---------- 3. Priority shown in the Attention queue (Overview) ----------
replace_once('app/workspace.tsx',
    '''<div className="queue-meta"><Badge status={t.status}/><small>{t.team}</small></div><ArrowUpRight size={17}/></button>)}</section>''',
    '''<div className="queue-meta"><Badge status={t.status}/><span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span><small>{t.team}</small></div><ArrowUpRight size={17}/></button>)}</section>''',
    "workspace.tsx: show priority in Attention queue")

# ---------- 4. Fix stretched logo / size the reporter photo properly ----------
replace_once('app/workspace.tsx',
    '''<div className="evidence"><img src={photoUrl||'/logo.png'} alt={photoUrl?'Reported photograph':'PaveLedger logo — no photograph uploaded yet'}/>{!photoUrl&&<span>No photograph uploaded yet</span>}</div>''',
    '''<div className="evidence"><img src={photoUrl||'/logo.png'} alt={photoUrl?'Reported photograph':'PaveLedger logo — no photograph uploaded yet'} style={photoUrl?{width:'100%',maxHeight:280,objectFit:'cover'}:{width:'100%',maxHeight:280,objectFit:'contain',background:'#f4f6f8',padding:24}}/>{!photoUrl&&<span>No photograph uploaded yet</span>}</div>''',
    "workspace.tsx: size the reporter photo / logo fallback correctly")

# ---------- 5. Make the four Overview metric cards clickable ----------
replace_once('app/workspace.tsx',
    '''<div className="metrics">{[{label:'Active investigations',value:active.length,sub:'Across your permitted scope',icon:ListChecks},{label:'Urgent attention',value:urgent.length,sub:'Safety action takes priority',icon:Camera},{label:'Awaiting verification',value:waiting.length,sub:'A clear repeat observation is needed',icon:CheckCircle2},{label:'Reopened cases',value:reopened.length,sub:'Includes previously reopened tickets',icon:RotateCcw}].map((k,i)=><div className={'metric metric-'+i} key={k.label}><div><span>{k.label}</span><k.icon size={19}/></div><strong>{k.value.toString().padStart(2,'0')}</strong><p>{k.sub}</p></div>)}</div>''',
    '''<div className="metrics">{[{label:'Active investigations',value:active.length,sub:'Across your permitted scope',icon:ListChecks,filterValue:'all'},{label:'Urgent attention',value:urgent.length,sub:'Safety action takes priority',icon:Camera,filterValue:'Urgent'},{label:'Awaiting verification',value:waiting.length,sub:'A clear repeat observation is needed',icon:CheckCircle2,filterValue:'Awaiting verification'},{label:'Reopened cases',value:reopened.length,sub:'Includes previously reopened tickets',icon:RotateCcw,filterValue:'ReopenedEver'}].map((k,i)=><button className={'metric metric-'+i} key={k.label} style={{cursor:'pointer',textAlign:'left',border:'none',background:'inherit',font:'inherit'}} onClick={()=>{setFilter(k.filterValue);setView('Investigations')}}><div><span>{k.label}</span><k.icon size={19}/></div><strong>{k.value.toString().padStart(2,'0')}</strong><p>{k.sub}</p></button>)}</div>''',
    "workspace.tsx: make Overview metric cards clickable")

# ---------- 6. Support the new sentinel filter values (Urgent, ReopenedEver) in the ticket list ----------
replace_once('app/workspace.tsx',
    "const filtered=tickets.filter(t=>(filter==='all'||t.status===filter)&&(t.id+' '+t.road+' '+t.title).toLowerCase().includes(q.toLowerCase()));",
    "const filtered=tickets.filter(t=>(filter==='all'||t.status===filter||(filter==='Urgent'&&t.severity==='Urgent')||(filter==='ReopenedEver'&&t.reopened>0))&&(t.id+' '+t.road+' '+t.title).toLowerCase().includes(q.toLowerCase()));",
    "workspace.tsx: filtered list understands Urgent/ReopenedEver sentinel filters")

# ---------- 7. Add a visible Teams list to the Teams & access page ----------
replace_once('app/workspace.tsx',
    '</div><Table><TableHeader><TableRow><TableHead>Member</TableHead>',
    '''</div><div className="team-grid">{data.teams.map(team=><div className="panel-mini" key={team}><h3>{team}</h3><small>{data.members.filter(m=>m.team===team&&isActive(m)).length} active members</small></div>)}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div><Table><TableHeader><TableRow><TableHead>Member</TableHead>''',
    "workspace.tsx: add Teams list panel above the member table")

# ---------- 8. Contractor column in the dashboard table ----------
replace_once('app/workspace.tsx',
    '''function TicketTable({tickets,onSelect,onPriority,canEditPriority,busy}:{tickets:Ticket[],onSelect:(id:string)=>void,onPriority:(id:string,severity:string)=>void,canEditPriority:boolean,busy:boolean}){return <Table><TableHeader><TableRow><TableHead>Investigation</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className="table-title" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small><small className="block muted">Updated {new Date(t.updated).toLocaleString()}</small></button></TableCell><TableCell>{canEditPriority?<select value={t.severity} disabled={busy} onChange={e=>onPriority(t.id,e.target.value)} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span>}</TableCell><TableCell><Badge status={t.status}/>{t.reopened>0&&<small className="block muted">Reopened ×{t.reopened}</small>}</TableCell><TableCell>{t.team}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className="icon-btn" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}''',
    '''function TicketTable({tickets,onSelect,onPriority,canEditPriority,busy}:{tickets:Ticket[],onSelect:(id:string)=>void,onPriority:(id:string,severity:string)=>void,canEditPriority:boolean,busy:boolean}){return <Table><TableHeader><TableRow><TableHead>Investigation</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Contractor</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className="table-title" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small><small className="block muted">Updated {new Date(t.updated).toLocaleString()}</small></button></TableCell><TableCell>{canEditPriority?<select value={t.severity} disabled={busy} onChange={e=>onPriority(t.id,e.target.value)} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span>}</TableCell><TableCell><Badge status={t.status}/>{t.reopened>0&&<small className="block muted">Reopened ×{t.reopened}</small>}</TableCell><TableCell>{t.team}</TableCell><TableCell>{t.contractor||'Unassigned'}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className="icon-btn" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}''',
    "workspace.tsx: add Contractor column to dashboard table")

# ---------- 9. Contractor state + assignment UI on the individual ticket ----------
replace_once('app/workspace.tsx',
    "const [photoUrl,setPhotoUrl]=useState<string|null>(null);",
    "const [photoUrl,setPhotoUrl]=useState<string|null>(null);\nconst [contractorPick,setContractorPick]=useState('none');",
    "workspace.tsx: add contractorPick state")

replace_once('app/workspace.tsx',
    '<div className="warranty-box"><ShieldCheck size={20}/><div><strong>{t.warranty}</strong><p>{t.contractor||\'No contractor established\'}</p></div></div>',
    '''<div className="warranty-box"><ShieldCheck size={20}/><div><strong>{t.warranty}</strong><p>{t.contractor||'No contractor established'}</p></div></div>{['Admin','Team lead'].includes(data.viewer.role)&&<div className="form"><Pick label="Assign contractor" value={contractorPick} onChange={setContractorPick} items={[{value:'none',label:'Choose a contract covering this road'},...data.contracts.filter(c=>c.road===t.road).map(c=>({value:c.id,label:c.id+' · '+c.contractor}))]}/><button className="secondary" disabled={busy||contractorPick==='none'} onClick={()=>mutate({action:'assignContractor',id:t.id,contractId:contractorPick})}>Assign contractor</button></div>}''',
    "workspace.tsx: add contractor assignment control to ticket detail")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.7",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Contractor is now shown as a column on the dashboard and assignable directly from the ticket page (Admin, Team lead)
- Archive/unarchive/request-archive controls moved to the bottom of each investigation
- Priority now shown in the Overview Attention queue
- Fixed the stretched logo image; reporter photos and the logo fallback are now sized correctly
- All four Overview metric cards are now clickable and jump to the matching filtered view
- Added a visible Teams list to the Teams & access page
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
