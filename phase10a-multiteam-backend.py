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

VERSION = "2.1.9"
TODAY = date.today().isoformat()

# ============================================================
# lib/domain.ts
# ============================================================

replace_once('lib/domain.ts',
    "export type Member={id:string,name:string,email:string,role:Role,team:string,contractor:string;vehicleTag?:string;notifyPrefs?:Record<string,boolean>;phone?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "export type Member={id:string,name:string,email:string,role:Role,teams:string[],contractor:string;vehicleTag?:string;notifyPrefs?:Record<string,boolean>;phone?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "domain.ts: Member.team -> Member.teams (array)")

replace_once('lib/domain.ts',
    "(['Team lead','Reviewer','Head Analyst'].includes(m.role)&&t.team===m.team)",
    "(['Team lead','Reviewer','Head Analyst'].includes(m.role)&&m.teams.includes(t.team))",
    "domain.ts: canSee checks m.teams.includes(t.team)")

replace_once('lib/domain.ts',
    "export function normalizeState(s:State){for(const m of s.members){m.active??=true;m.demo??=m.id.startsWith('demo-');}for(const t of s.tickets){t.evidence??=[];t.lane??='Lane 1';}return s;}",
    "export function normalizeState(s:State){for(const m of s.members){m.active??=true;m.demo??=m.id.startsWith('demo-');if(!Array.isArray((m as any).teams)){const legacy=(m as any).team;(m as any).teams=legacy?[legacy]:[];}delete (m as any).team;}for(const t of s.tickets){t.evidence??=[];t.lane??='Lane 1';}return s;}",
    "domain.ts: normalizeState migrates legacy single team to teams array")

# ============================================================
# lib/actions.ts
# ============================================================

replace_once('lib/actions.ts',
    "team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
    "teams:z.array(short).max(3).default([]),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
    "actions.ts: member schema accepts teams array (max 3)")

replace_once('lib/actions.ts',
    "if(['Team lead','Analyst','Reviewer','Head Analyst'].includes(v.role)&&!s.teams.includes(v.team))throw new AppError('Choose an existing team.');",
    "if(['Team lead','Analyst','Reviewer','Head Analyst'].includes(v.role)&&(!v.teams.length||v.teams.some(x=>!s.teams.includes(x))))throw new AppError('Choose one to three existing teams.');",
    "actions.ts: validate each team in the array exists")

replace_once('lib/actions.ts',
    "v.role!=='Analyst'||v.team!==existing.team)",
    "v.role!=='Analyst'||JSON.stringify([...v.teams].sort())!==JSON.stringify([...(existing.teams||[])].sort()))",
    "actions.ts: reassignment guard compares team arrays")

replace_once('lib/actions.ts',
    "const clean={...v,team:['Team lead','Analyst','Reviewer','Admin','Head Analyst'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};",
    "const clean={...v,teams:['Team lead','Analyst','Reviewer','Admin','Head Analyst'].includes(v.role)?v.teams:[],contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};",
    "actions.ts: clean object keeps teams array")

replace_once('lib/actions.ts',
    "if(!s.teams.includes(team)||(m.role==='Team lead'&&team!==m.team))throw new AppError('Choose an accessible team.');const a=body.analyst?s.members.find(x=>x.id===body.analyst&&x.role==='Analyst'&&x.team===team&&isActive(x)):null;",
    "if(!s.teams.includes(team)||(m.role==='Team lead'&&!m.teams.includes(team)))throw new AppError('Choose an accessible team.');const a=body.analyst?s.members.find(x=>x.id===body.analyst&&x.role==='Analyst'&&x.teams.includes(team)&&isActive(x)):null;",
    "actions.ts: assign action checks teams array")

replace_once('lib/actions.ts',
    "s.members.forEach(m=>{if(m.team===oldName)m.team=newName});",
    "s.members.forEach(m=>{if(m.teams?.includes(oldName))m.teams=m.teams.map(x=>x===oldName?newName:x)});",
    "actions.ts: teamUpdate cascades rename across teams arrays")

replace_once('lib/actions.ts',
    "if(s.members.some(x=>x.team===name&&isActive(x)))throw new AppError('Reassign or suspend all active members of this team before deleting it.');",
    "if(s.members.some(x=>x.teams?.includes(name)&&isActive(x)))throw new AppError('Reassign or suspend all active members of this team before deleting it.');",
    "actions.ts: teamDelete checks teams array")

# ============================================================
# lib/context.ts
# ============================================================

replace_once('lib/context.ts',
    "const members=s.members.filter(x=>['Admin','Auditor','Team lead','Director'].includes(m.role)||(m.role==='Reviewer'&&x.team===m.team)||x.id===m.id).map(x=>({...x,email:['Admin','Team lead','Director'].includes(m.role)?x.email:'',authUserId:['Admin','Team lead','Director'].includes(m.role)?x.authUserId:undefined}));",
    "const members=s.members.filter(x=>['Admin','Auditor','Team lead','Director'].includes(m.role)||(m.role==='Reviewer'&&x.teams?.some(t=>m.teams.includes(t)))||x.id===m.id).map(x=>({...x,email:['Admin','Team lead','Director'].includes(m.role)?x.email:'',authUserId:['Admin','Team lead','Director'].includes(m.role)?x.authUserId:undefined}));",
    "context.ts: Reviewer sees members sharing any team")

replace_once('lib/context.ts',
    "teams:['Admin','Auditor'].includes(m.role)?s.teams:m.team?[m.team]:[]",
    "teams:['Admin','Auditor'].includes(m.role)?s.teams:(m.teams||[])",
    "context.ts: teams list uses teams array")

# ============================================================
# version + changelog
# ============================================================

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.8",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Members can now belong to up to 3 teams instead of just one
- Existing single-team members are automatically migrated to the new teams array on next load
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. IMPORTANT: do not run npm run build yet if you plan to run the frontend")
print("script (phase10b) right after -- workspace.tsx still references the old")
print("single-team fields and will fail to compile until phase10b is applied too.")
print("If you want to check the backend alone compiles, expect TypeScript errors")
print("in app/workspace.tsx -- that's expected at this stage.")
