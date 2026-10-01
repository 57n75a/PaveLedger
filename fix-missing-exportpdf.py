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

replace_once('app/workspace.tsx',
    '''function exportCSV(){const rows=[['Ticket','Road','Status','Priority','Team','Latitude','Longitude','Reopens'],...filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.lat,t.lng,t.reopened])];download('PaveLedger_Tickets.csv',rows.map(r=>r.map(x=>'"'+String(x).replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"').join(',')).join('\\n'),'text/csv')}''',
    '''function exportCSV(){const rows=[['Ticket','Road','Status','Priority','Team','Latitude','Longitude','Reopens'],...filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.lat,t.lng,t.reopened])];download('PaveLedger_Tickets.csv',rows.map(r=>r.map(x=>'"'+String(x).replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"').join(',')).join('\\n'),'text/csv')}
function exportPDF(){const doc=new jsPDF();doc.setFontSize(14);doc.text('PaveLedger Tickets Export',14,15);doc.setFontSize(9);doc.text(new Date().toLocaleString(),14,21);autoTable(doc,{startY:26,head:[['Ticket','Road','Status','Priority','Team','Contractor','Observations']],body:filtered.map(t=>[t.id,t.road,t.status,t.severity,t.team,t.contractor||'Unassigned',String(t.observations)]),styles:{fontSize:8}});doc.save('PaveLedger_Tickets.pdf')}''',
    "workspace.tsx: add the missing exportPDF function")

print("\nDone. Now run:")
print("  npm run build")
