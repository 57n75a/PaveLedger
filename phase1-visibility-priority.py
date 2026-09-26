import pathlib

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

# ---------- lib/actions.ts: add 'priority' action ----------

replace_once('lib/actions.ts',
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}",
    "}else if(action==='priority'){\n   if(!isActive(m)||m.role==='Auditor')throw new AppError('This action is not permitted for your role.',403);\n   const sev=z.enum(['Urgent','Standard','Low']).parse(body.severity);t.severity=sev;event='Priority set to '+sev;\n  }else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}",
    "actions.ts: add priority action")

# ---------- app/workspace.tsx: TicketTable component ----------

replace_once('app/workspace.tsx',
    "function TicketTable({tickets,onSelect}:{tickets:Ticket[],onSelect:(id:string)=>void}){return <Table><TableHeader><TableRow><TableHead>Investigation</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className=\"table-title\" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small></button></TableCell><TableCell><span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span></TableCell><TableCell><Badge status={t.status}/></TableCell><TableCell>{t.team}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className=\"icon-btn\" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}",
    "function TicketTable({tickets,onSelect,onPriority,canEditPriority,busy}:{tickets:Ticket[],onSelect:(id:string)=>void,onPriority:(id:string,severity:string)=>void,canEditPriority:boolean,busy:boolean}){return <Table><TableHeader><TableRow><TableHead>Investigation</TableHead><TableHead>Priority</TableHead><TableHead>Stage</TableHead><TableHead>Assigned team</TableHead><TableHead>Observations</TableHead><TableHead/></TableRow></TableHeader><TableBody>{tickets.map(t=><TableRow key={t.id}><TableCell><button className=\"table-title\" onClick={()=>onSelect(t.id)}><strong>{t.road}</strong><small>{t.id}</small><small className=\"block muted\">Updated {new Date(t.updated).toLocaleString()}</small></button></TableCell><TableCell>{canEditPriority?<select value={t.severity} disabled={busy} onChange={e=>onPriority(t.id,e.target.value)} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity}</span>}</TableCell><TableCell><Badge status={t.status}/>{t.reopened>0&&<small className=\"block muted\">Reopened \u00d7{t.reopened}</small>}</TableCell><TableCell>{t.team}</TableCell><TableCell>{t.observations}</TableCell><TableCell><button aria-label={'Open '+t.id} className=\"icon-btn\" onClick={()=>onSelect(t.id)}><ArrowUpRight size={18}/></button></TableCell></TableRow>)}</TableBody></Table>}",
    "workspace.tsx: TicketTable gets timestamp row, priority select, reopened flag")

# ---------- app/workspace.tsx: TicketTable invocation ----------

replace_once('app/workspace.tsx',
    "<TicketTable tickets={filtered} onSelect={setSelected}/>",
    "<TicketTable tickets={filtered} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={role!=='Auditor'} busy={busy}/>",
    "workspace.tsx: wire new TicketTable props")

# ---------- app/workspace.tsx: Detail page priority + reopened flag ----------

replace_once('app/workspace.tsx',
    "<Badge status={t.status}/><span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity} priority</span></div>",
    "<Badge status={t.status}/>{data.viewer.role!=='Auditor'?<select value={t.severity} disabled={busy} onChange={e=>mutate({action:'priority',id:t.id,severity:e.target.value})} className={t.severity==='Urgent'?'priority-urgent':'muted'}><option>Urgent</option><option>Standard</option><option>Low</option></select>:<span className={t.severity==='Urgent'?'priority-urgent':'muted'}>{t.severity} priority</span>}{t.reopened>0&&<span className=\"muted\">\u00b7 Reopened \u00d7{t.reopened}</span>}</div>",
    "workspace.tsx: Detail page priority select and reopened flag")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
