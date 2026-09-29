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

# ============================================================
# 1. lib/actions.ts: re-add the missing assignContractor and cancelPendingClosure actions
# ============================================================
replace_once('lib/actions.ts',
    "event='Archive requested';}",
    "event='Archive requested';}else if(action==='assignContractor'){requireRole(['Admin','Team lead']);const contractId=short.parse(body.contractId);const contract=s.contracts.find(x=>x.id===contractId);const observed=t.created.slice(0,10);if(!contract||!contractCovers(contract,t)||contract.start>observed||contract.end<observed)throw new AppError('Choose a contract covering this ticket location and observation date.');t.contractor=contract.contractor;t.contractId=contract.id;if(t.warranty==='Needs review')t.warranty='Candidate match';event='Contractor assigned: '+contract.contractor;}else if(action==='cancelPendingClosure'){requireRole(['Admin','Team lead','Head Analyst','Analyst','Reviewer']);if(!t.autoCloseAt)throw new AppError('This ticket is not pending closure.');delete t.pendingClosureAt;delete t.autoCloseAt;delete t.pendingClosureEvidence;event='Pending closure cancelled';}",
    "actions.ts: restore assignContractor and add cancelPendingClosure")

# ============================================================
# 2. app/workspace.tsx: deduplicate the Edit contract dialog (keep one copy)
# ============================================================
WP = pathlib.Path('app/workspace.tsx')
wtext = WP.read_text()
marker = "<Dialog open={!!editingContract} onOpenChange={v=>!v&&setEditingContract(null)}>"
first = wtext.find(marker)
second = wtext.find(marker, first + 1) if first != -1 else -1
if first == -1:
    print("SKIP: could not find the Edit contract dialog at all")
elif second == -1:
    print("OK: only one copy of the Edit contract dialog found (no duplicate to remove)")
else:
    block_len = second - first
    duplicate = wtext[second:second + block_len]
    original_block = wtext[first:second]
    if duplicate == original_block:
        wtext = wtext[:second] + wtext[second + block_len:]
        WP.write_text(wtext)
        print(f"OK: removed the duplicate Edit contract dialog ({block_len} characters)")
    else:
        print("SKIP: found two copies but they are not identical -- not removing automatically")

# ============================================================
# 3. app/workspace.tsx: add phone/address/country/map picker to the (now single) Edit contract dialog
# ============================================================
replace_once('app/workspace.tsx',
    '''{['contractor','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required defaultValue={(editingContract as any)[x]} type={x==='email'?'email':'text'}/></label>)}<div className="two-cols">''',
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={x!=='phone'} defaultValue={(editingContract as any)[x]||''} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}<label>Address<input name="address" defaultValue={editingContract.address||''} placeholder="Street, city"/></label><label>Country or region<select name="addressCountry" defaultValue={editingContract.addressCountry==='Europe'?'EU':(editingContract.addressCountry||'USA')}><option value="USA">USA</option><option value="CAN">Canada</option><option value="SRB">Serbia</option><option value="EU">EU</option></select></label><ScopeLocator key={editingContract.id} initialLat={editingContract.scopeLat??undefined} initialLng={editingContract.scopeLng??undefined} initialRadius={editingContract.scopeRadius??undefined}/><div className="two-cols">''',
    "workspace.tsx: Edit contract dialog gets phone/address/country/map picker")

# ============================================================
# 4. app/workspace.tsx: clean up the leftover photoUrl state/effect in Detail (contractorPick sits between them)
# ============================================================
replace_once('app/workspace.tsx',
    '''const [photoUrl,setPhotoUrl]=useState<string|null>(null);
const [contractorPick,setContractorPick]=useState('none');
useEffect(()=>{let active=true;const first=(t.evidence||[])[0];if(!first){setPhotoUrl(null);return}authorizedFetch('/api/evidence?ticket='+encodeURIComponent(t.id)+'&id='+encodeURIComponent(first.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active)setPhotoUrl(d.url||null)}).catch(()=>{if(active)setPhotoUrl(null)});return()=>{active=false}},[t.id,t.evidence,persona]);''',
    '''const [contractorPick,setContractorPick]=useState('none');''',
    "workspace.tsx: remove leftover photoUrl state/effect from Detail")

print("\nDone. Now run:")
print("  npm run build")
