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

VERSION = "2.0.9"
TODAY = date.today().isoformat()

# ============================================================
# lib/domain.ts
# ============================================================

replace_once('lib/domain.ts',
    "vehicleTag?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;active?:boolean;authUserId?:string;demo?:boolean};",
    "domain.ts: add notifyPrefs to Member type")

dp = pathlib.Path('lib/domain.ts')
domain_text = dp.read_text()
if 'export function wantsNotification' not in domain_text:
    dp.write_text(domain_text + "\nexport function wantsNotification(m:Member,key:string):boolean{if(m.role==='Vehicle')return false;const prefs=m.notifyPrefs;const def=key==='assignment'||key==='statusChange';return prefs&&key in prefs?!!prefs[key]:def;}\n")
    print("OK: appended wantsNotification helper to domain.ts")
else:
    print("SKIP: wantsNotification already present in domain.ts")

# ============================================================
# lib/actions.ts
# ============================================================

replace_once('lib/actions.ts',
    "import {canSee,permitted,isActive,closed,eligibleVerification,roles,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "import {canSee,permitted,isActive,closed,eligibleVerification,roles,wantsNotification,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "actions.ts: import wantsNotification")

# selfProfile + notifyPrefs early-return actions
replace_once('lib/actions.ts',
    "const t=s.tickets.find(x=>x.id===body.id);if(!t||!canSee(t,m))throw new AppError('Ticket not accessible.',403);",
    "if(action==='selfProfile'){const name=short.parse(body.name);actual.name=name;s.events.unshift({at:now,actor,action:'Profile name updated: '+name});return}if(action==='notifyPrefs'){actual.notifyPrefs={assignment:body.assignment===true||body.assignment==='true',statusChange:body.statusChange===true||body.statusChange==='true',manualEdit:body.manualEdit===true||body.manualEdit==='true'};s.events.unshift({at:now,actor,action:'Notification preferences updated'});return}const t=s.tickets.find(x=>x.id===body.id);if(!t||!canSee(t,m))throw new AppError('Ticket not accessible.',403);",
    "actions.ts: add selfProfile and notifyPrefs actions")

# assign: respect assignment preference + notify the team lead who assigned
replace_once('lib/actions.ts',
    "if(a)s.notifications.unshift({id:crypto.randomUUID(),recipient:a.id,ticket:t.id,text:`Assigned to you: ${t.road}`,at:now});event='Assignment updated';",
    "if(a&&wantsNotification(a,'assignment'))s.notifications.unshift({id:crypto.randomUUID(),recipient:a.id,ticket:t.id,text:`Assigned to you: ${t.road}`,at:now});if(m.role==='Team lead')s.notifications.unshift({id:crypto.randomUUID(),recipient:m.id,ticket:t.id,text:`You assigned ${t.road} to ${a?a.name:'the team queue'}`,at:now});event='Assignment updated';",
    "actions.ts: assignment preference + team lead self-notification")

# transition: respect statusChange preference
replace_once('lib/actions.ts',
    "t.status=next as Status;event=t.status;if(t.analyst)s.notifications.unshift({id:crypto.randomUUID(),recipient:t.analyst,ticket:t.id,text:`Status changed: ${t.road} is now ${next}`,at:now});",
    "t.status=next as Status;event=t.status;if(t.analyst){const analystMember=s.members.find(x=>x.id===t.analyst);if(analystMember&&wantsNotification(analystMember,'statusChange'))s.notifications.unshift({id:crypto.randomUUID(),recipient:t.analyst,ticket:t.id,text:`Status changed: ${t.road} is now ${next}`,at:now});}",
    "actions.ts: statusChange preference")

# note: manualEdit notification
replace_once('lib/actions.ts',
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}",
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';if(t.analyst&&t.analyst!==actual.id){const am=s.members.find(x=>x.id===t.analyst);if(am&&wantsNotification(am,'manualEdit'))s.notifications.unshift({id:crypto.randomUUID(),recipient:am.id,ticket:t.id,text:`Note added to your case: ${t.road}`,at:now});}}",
    "actions.ts: manualEdit notification on note")

# priority: manualEdit notification
replace_once('lib/actions.ts',
    "const sev=z.enum(['Urgent','Standard','Low']).parse(body.severity);t.severity=sev;event='Priority set to '+sev;",
    "const sev=z.enum(['Urgent','Standard','Low']).parse(body.severity);t.severity=sev;event='Priority set to '+sev;if(t.analyst&&t.analyst!==actual.id){const am=s.members.find(x=>x.id===t.analyst);if(am&&wantsNotification(am,'manualEdit'))s.notifications.unshift({id:crypto.randomUUID(),recipient:am.id,ticket:t.id,text:`Priority changed on your case: ${t.road}`,at:now});}",
    "actions.ts: manualEdit notification on priority change")

# member/memberUpdate: allow Team lead and Director, block granting/modifying Admin
replace_once('lib/actions.ts',
    "requireRole(['Admin']);if(actual.id!==m.id)throw new AppError('Return to your own administrator identity before changing access.',403);",
    "requireRole(['Admin','Team lead','Director']);if(actual.id!==m.id)throw new AppError('Return to your own identity before changing access.',403);",
    "actions.ts: Team lead and Director can edit member access")

replace_once('lib/actions.ts',
    "const v=z.object({name:short,email:z.string().trim().email().max(250).transform(x=>x.toLowerCase()),role:z.enum(roles as [typeof roles[number],...typeof roles[number][]]),team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
    "const v=z.object({name:short,email:z.string().trim().email().max(250).transform(x=>x.toLowerCase()),role:z.enum(roles as [typeof roles[number],...typeof roles[number][]]),team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);\n  if(m.role!=='Admin'&&v.role==='Admin')throw new AppError('Only an administrator can grant Administrator access.',403);",
    "actions.ts: only Admin can grant Admin role")

replace_once('lib/actions.ts',
    "const existing=action==='memberUpdate'?s.members.find(x=>x.id===body.memberId):undefined;if(action==='memberUpdate'&&!existing)throw new AppError('Member not found.');",
    "const existing=action==='memberUpdate'?s.members.find(x=>x.id===body.memberId):undefined;if(action==='memberUpdate'&&!existing)throw new AppError('Member not found.');\n  if(m.role!=='Admin'&&existing?.role==='Admin')throw new AppError('Only an administrator can modify Administrator access.',403);",
    "actions.ts: only Admin can modify an existing Admin")

# ============================================================
# lib/context.ts: Team lead / Director see all members, not just their team
# ============================================================

replace_once('lib/context.ts',
    "const members=s.members.filter(x=>m.role==='Admin'||m.role==='Auditor'||(['Team lead','Reviewer'].includes(m.role)&&x.team===m.team)||x.id===m.id).map(x=>({...x,email:m.role==='Admin'?x.email:'',authUserId:m.role==='Admin'?x.authUserId:undefined}));",
    "const members=s.members.filter(x=>['Admin','Auditor','Team lead','Director'].includes(m.role)||(m.role==='Reviewer'&&x.team===m.team)||x.id===m.id).map(x=>({...x,email:['Admin','Team lead','Director'].includes(m.role)?x.email:'',authUserId:['Admin','Team lead','Director'].includes(m.role)?x.authUserId:undefined}));",
    "context.ts: Team lead and Director see all members org-wide")

# ============================================================
# version + changelog
# ============================================================

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.8",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added self-service profile name updates (email still locked)
- Added configurable notification preferences: assignment and status-change on by default, manual-edit notifications off by default
- Team lead now gets notified when they personally assign a ticket
- Team lead and Director can now edit any member's access and see all members org-wide, but cannot grant or modify Administrator access
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
