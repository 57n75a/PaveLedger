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

# Add photoUrl state + effect to fetch the ticket's first evidence photo
replace_once('app/workspace.tsx',
    "const [note,setNote]=useState(''),[next,setNext]=useState('none'),[team,setTeam]=useState(t.team),[analyst,setAnalyst]=useState(t.analyst||'none'),[contract,setContract]=useState('none'),[confirmed,setConfirmed]=useState(false),[verified,setVerified]=useState(false),[evidenceId,setEvidenceId]=useState('none'),[duplicateOf,setDuplicateOf]=useState('none'),[shared,setShared]=useState(false);",
    "const [note,setNote]=useState(''),[next,setNext]=useState('none'),[team,setTeam]=useState(t.team),[analyst,setAnalyst]=useState(t.analyst||'none'),[contract,setContract]=useState('none'),[confirmed,setConfirmed]=useState(false),[verified,setVerified]=useState(false),[evidenceId,setEvidenceId]=useState('none'),[duplicateOf,setDuplicateOf]=useState('none'),[shared,setShared]=useState(false);\nconst [photoUrl,setPhotoUrl]=useState<string|null>(null);\nuseEffect(()=>{let active=true;const first=(t.evidence||[])[0];if(!first){setPhotoUrl(null);return}authorizedFetch('/api/evidence?ticket='+encodeURIComponent(t.id)+'&id='+encodeURIComponent(first.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active)setPhotoUrl(d.url||null)}).catch(()=>{if(active)setPhotoUrl(null)});return()=>{active=false}},[t.id,t.evidence,persona]);",
    "workspace.tsx: Detail fetches first reporter photo")

# Replace the static demo image with the real photo (or logo fallback)
replace_once('app/workspace.tsx',
    "<div className=\"evidence\"><img src=\"/pothole-demo.png\" alt=\"Generated pothole illustration used as demonstration evidence\"/><span>Generated illustration · not a real report</span></div>",
    "<div className=\"evidence\"><img src={photoUrl||'/logo.png'} alt={photoUrl?'Reported photograph':'PaveLedger logo \u2014 no photograph uploaded yet'}/>{!photoUrl&&<span>No photograph uploaded yet</span>}</div>",
    "workspace.tsx: Detail shows real photo or logo fallback")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
