import pathlib

path = 'app/workspace.tsx'
p = pathlib.Path(path)
text = p.read_text()

corrupted = "Reviewer:'Independently veri{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects'}[m.role]}fy team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records'}[m.role]"

fixed = "Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects'}[m.role]"

count = text.count(corrupted)
if count != 1:
    print(f"ABORT: expected exactly 1 match of the corrupted text, found {count}. No changes made.")
    print("Paste the output of: sed -n '43p' app/workspace.tsx  so this can be re-checked.")
else:
    text = text.replace(corrupted, fixed, 1)
    p.write_text(text)
    print("OK: line 43 repaired.")
