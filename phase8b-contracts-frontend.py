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

VERSION = "2.1.2"
TODAY = date.today().isoformat()

# ---------- 1. Derive topTicket for the hero ----------
replace_once('app/workspace.tsx',
    "const allTickets=data?.tickets||[],tickets=allTickets.filter(t=>!t.archived),archivedTickets=allTickets.filter(t=>t.archived),active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification'),mine=tickets.filter(t=>t.analyst===data?.viewer.id||t.reportedBy===data?.viewer.id||t.completedBy===data?.viewer.id||t.closedBy===data?.viewer.id);",
    "const allTickets=data?.tickets||[],tickets=allTickets.filter(t=>!t.archived),archivedTickets=allTickets.filter(t=>t.archived),active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification'),mine=tickets.filter(t=>t.analyst===data?.viewer.id||t.reportedBy===data?.viewer.id||t.completedBy===data?.viewer.id||t.closedBy===data?.viewer.id),topTicket=[...active].sort((a,b)=>(b.severity==='Urgent'?1:0)-(a.severity==='Urgent'?1:0))[0];",
    "workspace.tsx: derive topTicket for the Overview hero")

# ---------- 2. Replace the static feature-card with a HeroTicket component ----------
replace_once('app/workspace.tsx',
    '''<section className="feature-card"><div className="image-wrap"><img src="/pothole-demo.png" alt="Generated illustration of a pothole in an asphalt road"/><span className="image-label">ILLUSTRATIVE CAMERA EVIDENCE</span></div><div className="feature-content"><p className="eyebrow">FROM OBSERVATION TO ACTION</p><h2>The image starts the investigation.</h2><p>Review the location, establish responsibility, and close the case only when the repair is verified.</p><button className="secondary" onClick={()=>setSelected(tickets[0]?.id)}>Inspect a report <ArrowUpRight size={16}/></button></div></section>''',
    '''<HeroTicket ticket={topTicket} persona={persona} onOpen={()=>topTicket&&setSelected(topTicket.id)}/>''',
    "workspace.tsx: replace static feature-card with HeroTicket")

# ---------- 3. Add the HeroTicket component ----------
replace_once('app/workspace.tsx',
    "function TicketTable(",
    '''function HeroTicket({ticket,persona,onOpen}:{ticket:Ticket|undefined,persona:string,onOpen:()=>void}){
 const [url,setUrl]=useState<string|null>(null);
 useEffect(()=>{let active=true;const first=(ticket?.evidence||[])[0];if(!ticket||!first){setUrl(null);return}authorizedFetch('/api/evidence?ticket='+encodeURIComponent(ticket.id)+'&id='+encodeURIComponent(first.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active)setUrl(d.url||null)}).catch(()=>{if(active)setUrl(null)});return()=>{active=false}},[ticket?.id,persona]);
 if(!ticket)return <section className="feature-card"><div className="image-wrap"><img src="/logo.png" alt="PaveLedger" style={{objectFit:'contain',padding:24,background:'#f4f6f8'}}/><span className="image-label">NO ACTIVE CASES</span></div><div className="feature-content"><p className="eyebrow">ALL CLEAR</p><h2>Nothing needs attention right now.</h2><p>New investigations will appear here as they come in.</p></div></section>;
 return <section className="feature-card"><div className="image-wrap"><img src={url||'/logo.png'} alt={url?'Top priority case photograph':'PaveLedger logo'} style={url?{objectFit:'cover'}:{objectFit:'contain',padding:24,background:'#f4f6f8'}}/><span className="image-label">TOP PRIORITY CASE</span></div><div className="feature-content"><p className="eyebrow">{ticket.severity.toUpperCase()} \u00b7 {ticket.status}</p><h2>{ticket.road}</h2><p>{ticket.title} \u00b7 reported {new Date(ticket.created).toLocaleDateString()}</p><button className="secondary" onClick={onOpen}>Inspect this case <ArrowUpRight size={16}/></button></div></section>;
}
function TicketTable(''',
    "workspace.tsx: add HeroTicket component")

# ---------- 4. Contractor picker: add heading + empty-state hint ----------
replace_once('app/workspace.tsx',
    '''{['Admin','Team lead'].includes(data.viewer.role)&&<div className="form"><Pick label="Assign contractor" value={contractorPick} onChange={setContractorPick} items={[{value:'none',label:'Choose a contract covering this road'},...data.contracts.filter(c=>c.road===t.road).map(c=>({value:c.id,label:c.id+' \u00b7 '+c.contractor}))]}/><button className="secondary" disabled={busy||contractorPick==='none'} onClick={()=>mutate({action:'assignContractor',id:t.id,contractId:contractorPick})}>Assign contractor</button></div>}''',
    '''{['Admin','Team lead'].includes(data.viewer.role)&&<div className="form"><h3>Contractor &amp; warranty</h3><Pick label="Assign contractor" value={contractorPick} onChange={setContractorPick} items={[{value:'none',label:'Choose a contract covering this road'},...data.contracts.filter(c=>c.road===t.road).map(c=>({value:c.id,label:c.id+' \u00b7 '+c.contractor}))]}/><button className="secondary" disabled={busy||contractorPick==='none'} onClick={()=>mutate({action:'assignContractor',id:t.id,contractId:contractorPick})}>Assign contractor</button>{!data.contracts.some(c=>c.road===t.road)&&<p className="footnote">No contracts registered for "{t.road}" yet. Register one under Contracts, using the exact same road name, then it will appear here.</p>}</div>}''',
    "workspace.tsx: contractor picker heading + empty-state explanation")

# ---------- 5. Add editingContract state ----------
replace_once('app/workspace.tsx',
    "[contractOpen,setContractOpen]=useState(false),[contactOpen,setContactOpen]=useState(false),[globalQuery,setGlobalQuery]=useState(''),[profileOpen,setProfileOpen]=useState(false),[notifyOpen,setNotifyOpen]=useState(false);",
    "[contractOpen,setContractOpen]=useState(false),[contactOpen,setContactOpen]=useState(false),[globalQuery,setGlobalQuery]=useState(''),[profileOpen,setProfileOpen]=useState(false),[notifyOpen,setNotifyOpen]=useState(false),[editingContract,setEditingContract]=useState<any>(null);",
    "workspace.tsx: add editingContract state")

# ---------- 6. Add Edit button + notes/documents display to each contract card ----------
replace_once('app/workspace.tsx',
    '''<dl><div><dt>Warranty period</dt><dd>{c.start} to {c.end}</dd></div><div><dt>Point of contact</dt><dd>{c.poc}</dd></div><div><dt>Contact email</dt><dd>{c.email}</dd></div></dl></article>''',
    '''<dl><div><dt>Warranty period</dt><dd>{c.start} to {c.end}</dd></div><div><dt>Point of contact</dt><dd>{c.poc}</dd></div><div><dt>Contact email</dt><dd>{c.email}</dd></div></dl>{c.notes&&<p className="footnote">{c.notes}</p>}{!!c.documents?.length&&<p className="footnote">{c.documents.length} document(s) attached</p>}{role==='Admin'&&<button className="secondary" onClick={()=>setEditingContract(c)}>Edit contract</button>}</article>''',
    "workspace.tsx: add Edit button and notes/documents display to contract cards")

# ---------- 7. EditContractDocuments component + Contract edit Dialog ----------
replace_once('app/workspace.tsx',
    "function TicketTable(",
    '''function EditContractDocuments({contract,data,reload,persona}:{contract:any,data:any,reload:()=>void,persona:string}){
 const [uploading,setUploading]=useState(false),[err,setErr]=useState('');
 const suffix=persona==='owner'?'':'?persona='+encodeURIComponent(persona);
 async function openDoc(id:string){try{const r=await authorizedFetch('/api/contract-document?contract='+encodeURIComponent(contract.id)+'&id='+encodeURIComponent(id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona)));const d=await r.json();if(!r.ok)throw new Error(d.error);window.open(d.url,'_blank','noopener,noreferrer')}catch(e){setErr((e as Error).message)}}
 return <div className="evidence-panel"><h3>Contract documents</h3>{!(contract.documents||[]).length&&<p className="muted">No documents uploaded.</p>}{(contract.documents||[]).map((d:any)=><div className="evidence-row" key={d.id}><button className="text-button" onClick={()=>openDoc(d.id)}>{d.name}</button><small>{(d.bytes/1024).toFixed(0)} KB</small></div>)}<form className="form" onSubmit={async e=>{e.preventDefault();const form=e.currentTarget;setErr('');setUploading(true);try{const body=new FormData(form);body.set('contract',contract.id);body.set('revision',String(data.revision));const r=await authorizedFetch('/api/contract-document'+suffix,{method:'POST',body});const d=await r.json();if(!r.ok)throw new Error(d.error);form.reset();await reload()}catch(e){setErr((e as Error).message)}finally{setUploading(false)}}}><label>Upload document (contract PDF, addendum, etc.)<input type="file" name="file" required/></label><button className="secondary" disabled={uploading}>{uploading?'Uploading\u2026':'Upload document'}</button></form>{err&&<p role="alert" className="access-error">{err}</p>}</div>;
}
function TicketTable(''',
    "workspace.tsx: add EditContractDocuments component")

replace_once('app/workspace.tsx',
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={!!editingContract} onOpenChange={v=>!v&&setEditingContract(null)}><DialogContent><DialogHeader><DialogTitle>Edit contract {editingContract?.id}</DialogTitle><DialogDescription>Update contract details, attach documents, and link existing incidents on this road.</DialogDescription></DialogHeader>{editingContract&&data&&<><form className="form" onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const f=Object.fromEntries(fd);const linkTicketIds=data.tickets.filter((t:Ticket)=>t.road===editingContract.road).map((t:Ticket)=>t.id).filter((id:string)=>fd.has('link_'+id));if(await mutate({action:'contractUpdate',contractId:editingContract.id,...f,linkTicketIds}))setEditingContract(null)}}>{['contractor','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required defaultValue={(editingContract as any)[x]} type={x==='email'?'email':'text'}/></label>)}<div className="two-cols"><label>Warranty begins<input name="start" type="date" required defaultValue={editingContract.start}/></label><label>Warranty ends<input name="end" type="date" required defaultValue={editingContract.end}/></label></div><label>Additional notes<textarea name="notes" defaultValue={editingContract.notes||''} placeholder="Internal notes about this contract\u2026"/></label>{data.tickets.filter((t:Ticket)=>t.road===editingContract.road).length>0&&<div><p className="footnote">Link existing incidents on {editingContract.road}:</p>{data.tickets.filter((t:Ticket)=>t.road===editingContract.road).map((t:Ticket)=><label className="check" key={t.id}><input type="checkbox" name={'link_'+t.id} defaultChecked={t.contractId===editingContract.id}/>{t.id} \u00b7 {t.title}</label>)}</div>}<button className="primary" disabled={busy}>Save contract</button></form><EditContractDocuments contract={editingContract} data={data} reload={load} persona={persona}/></>}</DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add contract edit Dialog")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.1",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Overview now features a live "top priority case" hero with the real reported photo, instead of a static illustration
- Contractor assignment on a ticket now explains clearly when no matching contract exists for that road
- Contracts can now be edited: update details, add notes, upload documents, and link existing incidents on the same road
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
