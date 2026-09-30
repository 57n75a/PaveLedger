import pathlib, re
from datetime import date

VERSION = "2.4.3"
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

def replace_all(path, old, new, label, expected_min=1):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count < expected_min:
        print(f"SKIP ({count} matches, expected at least {expected_min}): {label} in {path}")
        return False
    p.write_text(text.replace(old, new))
    print(f"OK: {label} ({count} occurrence(s))")
    return True

WP = 'app/workspace.tsx'

# ---------- 1. Every dialog gets a max height + internal scroll, so Save is never hidden off-screen ----------
replace_all(WP,
    "<DialogContent>",
    "<DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}>",
    "workspace.tsx: all dialogs get a scrollable max-height so buttons stay reachable",
    expected_min=2)

# ---------- 2. Scope is optional in the create dialog: relax required + relabel ----------
replace_once(WP,
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={x!=='phone'} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}''',
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope (optional \u2014 e.g. corner of A St and C St to B St and C St, or leave blank if using the map radius)',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={!['phone','scope'].includes(x)} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}''',
    "workspace.tsx: contract create dialog -- scope optional, relabeled")

# ---------- 3. Scope is optional in the edit dialog: relax required + relabel ----------
replace_once(WP,
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={x!=='phone'} defaultValue={(editingContract as any)[x]||''} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}''',
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope (optional \u2014 e.g. corner of A St and C St to B St and C St, or leave blank if using the map radius)',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={!['phone','scope'].includes(x)} defaultValue={(editingContract as any)[x]||''} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}''',
    "workspace.tsx: contract edit dialog -- scope optional, relabeled")

# ---------- 4. Contract card: contractor name as the primary heading, road secondary ----------
replace_once(WP,
    "<small>{c.id}</small><h2>{c.road}</h2><h3>{c.contractor}</h3><p>{c.scope}</p>",
    "<small>{c.id}</small><h2>{c.contractor}</h2><h3>{c.road}</h3><p>{c.scope||'No work-scope description provided.'}</p>",
    "workspace.tsx: contract card shows contractor name first")

# ---------- 5. Rename team -> Edit team ----------
replace_once(WP,
    '<button className="secondary" onClick={()=>setEditingTeam(team)}>Rename team</button>',
    '<button className="secondary" onClick={()=>setEditingTeam(team)}>Edit team</button>',
    "workspace.tsx: 'Rename team' -> 'Edit team'")

# ---------- 6. TicketTable: add a stage-change dropdown ----------
replace_once(WP,
    '''function TicketTable({tickets,onSelect,onPriority,canEditPriority,busy}:{tickets:Ticket[],onSelect:(id:string)=>void,onPriority:(id:string,severity:string)=>void,canEditPriority:boolean,busy:boolean}){return <Table><TableHeader><TableRow><TableHead>Ticket</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Contractor</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className="table-title" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small><small className="block muted">Updated {new Date(t.updated).toLocaleString()}</small></button></TableCell><TableCell>{canEditPriority?<select value={t.severity} disabled={busy} onChange={e=>onPriority(t.id,e.target.value)} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span>}</TableCell><TableCell><Badge status={t.status}/>{t.reopened>0&&<small className="block muted">Reopened \u00d7{t.reopened}</small>}</TableCell><TableCell>{t.team}</TableCell><TableCell>{t.contractor||'Unassigned'}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className="icon-btn" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}''',
    '''function TicketTable({tickets,onSelect,onPriority,canEditPriority,busy,viewer,onStageChange}:{tickets:Ticket[],onSelect:(id:string)=>void,onPriority:(id:string,severity:string)=>void,canEditPriority:boolean,busy:boolean,viewer:Member,onStageChange:(t:Ticket,stage:string)=>void}){const stageOptions=(t:Ticket)=>nextStages(t).filter(s=>permitted(viewer,t,s));return <Table><TableHeader><TableRow><TableHead>Ticket</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Contractor</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className="table-title" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small><small className="block muted">Updated {new Date(t.updated).toLocaleString()}</small></button></TableCell><TableCell>{canEditPriority?<select value={t.severity} disabled={busy} onChange={e=>onPriority(t.id,e.target.value)} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span>}</TableCell><TableCell><Badge status={t.status}/>{t.reopened>0&&<small className="block muted">Reopened \u00d7{t.reopened}</small>}</TableCell>{stageOptions(t).length>0&&<select value="" disabled={busy} onChange={e=>{const v=e.target.value;if(v)onStageChange(t,v)}} style={{display:'block',marginTop:4,fontSize:12,width:'100%'}}><option value="">Change stage...</option>{stageOptions(t).map(s=><option key={s} value={s}>{s}</option>)}</select>}<TableCell>{t.team}</TableCell><TableCell>{t.contractor||'Unassigned'}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className="icon-btn" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}''',
    "workspace.tsx: TicketTable gets a stage-change dropdown")

# ---------- 7. Wire the Tickets-view TicketTable call site ----------
replace_once(WP,
    "<TicketTable tickets={filtered} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={role!=='Auditor'} busy={busy}/>",
    '''<TicketTable tickets={filtered} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={role!=='Auditor'} busy={busy} viewer={data.viewer} onStageChange={(tk,stage)=>{const SPECIAL=['Notice prepared','Duplicate','Verified closed'];if(SPECIAL.includes(stage)){toast.error('Open this ticket to provide the details this stage needs.');setSelected(tk.id);return}mutate({action:'transition',id:tk.id,status:stage,note:'Stage updated from the dashboard by '+data.viewer.name+'.'})}}/>''',
    "workspace.tsx: wire stage dropdown on the Tickets view")

# ---------- 8. Wire the Archive-view TicketTable call site ----------
replace_once(WP,
    "<TicketTable tickets={archivedTickets} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={false} busy={busy}/>",
    "<TicketTable tickets={archivedTickets} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={false} busy={busy} viewer={data.viewer} onStageChange={()=>{}}/>",
    "workspace.tsx: wire (no-op) stage dropdown prop on the Archive view")

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
- Fixed: edit dialogs (users, contracts) could overflow the screen on desktop with the Save button unreachable; every dialog now scrolls internally instead
- Contract create/edit forms no longer require the scope description; it's now a free-form optional field (e.g. cross-street description) alongside the map radius
- Contract cards now show the contractor's name as the heading, with the road as a subheading
- "Rename team" is now "Edit team"
- The main Tickets dashboard now has a stage-change dropdown per row for straightforward transitions; stages needing extra details (Notice prepared, Duplicate, Verified closed) open the full ticket instead
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
