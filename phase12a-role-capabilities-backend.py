import pathlib, re
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

VERSION = "2.4.0"
TODAY = date.today().isoformat()

# ============================================================
# lib/domain.ts: capability system
# ============================================================
replace_once('lib/domain.ts',
    "export type State={tickets:Ticket[],members:Member[],teams:string[],",
    "export type State={tickets:Ticket[],members:Member[],teams:string[],rolePermissions?:Record<string,string[]>,",
    "domain.ts: State gets rolePermissions")

caps_code = r"""
export const CAPABILITIES=['create','comment','assign','escalate','archive','contracts'] as const;
export type Capability=typeof CAPABILITIES[number];
export const DEFAULT_ROLE_CAPS:Record<Capability,Role[]>={
 create:['Admin','Team lead','Analyst'],
 comment:['Admin','Team lead','Analyst','Head Analyst','Reviewer'],
 assign:['Admin','Team lead'],
 escalate:['Head Analyst','Team lead'],
 archive:['Admin','Team lead','Director'],
 contracts:['Admin'],
};
export function roleCan(s:State,role:string,cap:Capability):boolean{const perms=s.rolePermissions?.[role];if(perms)return perms.includes(cap);return (DEFAULT_ROLE_CAPS[cap]||[]).includes(role as Role)}
"""
dp = pathlib.Path('lib/domain.ts')
dtext = dp.read_text()
if 'export const CAPABILITIES' in dtext:
    print("SKIP: capability system already present in domain.ts")
else:
    dp.write_text(dtext + caps_code)
    print("OK: domain.ts: added CAPABILITIES, DEFAULT_ROLE_CAPS, roleCan")

# ============================================================
# lib/actions.ts: use capabilities for the curated, safe-to-configure actions
# ============================================================
A = 'lib/actions.ts'

replace_once(A,
    "wantsNotification,contractCovers,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "wantsNotification,contractCovers,roleCan,CAPABILITIES,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "actions.ts: import roleCan and CAPABILITIES")

replace_once(A,
    "if(action==='create'){\n  requireRole(['Admin','Team lead','Analyst']);",
    "if(action==='create'){\n  if(!isActive(m)||!roleCan(s,m.role,'create'))throw new AppError('This action is not permitted for your role.',403);",
    "actions.ts: create ticket uses 'create' capability")

replace_once(A,
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Head Analyst','Reviewer']);noteField.parse(note);",
    "}else if(action==='note'){if(!isActive(m)||!roleCan(s,m.role,'comment'))throw new AppError('This action is not permitted for your role.',403);noteField.parse(note);",
    "actions.ts: comment action uses 'comment' capability")

replace_once(A,
    "if(action==='assign'){\n   requireRole(['Admin','Team lead']);",
    "if(action==='assign'){\n   if(!isActive(m)||!roleCan(s,m.role,'assign'))throw new AppError('This action is not permitted for your role.',403);",
    "actions.ts: assign uses 'assign' capability")

replace_once(A,
    "}else if(action==='escalate'){const targetRole=",
    "}else if(action==='escalate'){if(!isActive(m)||!roleCan(s,m.role,'escalate'))throw new AppError('This action is not permitted for your role.',403);const targetRole=",
    "actions.ts: escalate gated by 'escalate' capability (chain itself stays Head Analyst -> Team lead -> Director)")

replace_once(A,
    "}else if(action==='archive'){requireRole(['Admin','Team lead','Director']);",
    "}else if(action==='archive'){if(!isActive(m)||!roleCan(s,m.role,'archive'))throw new AppError('This action is not permitted for your role.',403);",
    "actions.ts: archive uses 'archive' capability")

replace_once(A,
    "}else if(action==='unarchive'){requireRole(['Admin','Team lead','Director']);",
    "}else if(action==='unarchive'){if(!isActive(m)||!roleCan(s,m.role,'archive'))throw new AppError('This action is not permitted for your role.',403);",
    "actions.ts: unarchive uses 'archive' capability")

replace_once(A,
    "}else if(action==='assignContractor'){requireRole(['Admin','Team lead']);",
    "}else if(action==='assignContractor'){if(!isActive(m)||!roleCan(s,m.role,'contracts'))throw new AppError('This action is not permitted for your role.',403);",
    "actions.ts: assignContractor uses 'contracts' capability")

replace_once(A,
    "requireRole(['Admin']);const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:",
    "if(!isActive(m)||!roleCan(s,m.role,'contracts'))throw new AppError('This action is not permitted for your role.',403);const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:",
    "actions.ts: contract create uses 'contracts' capability")

replace_once(A,
    "requireRole(['Admin']);const contractId=short.parse(body.contractId);const existing=s.contracts.find(x=>x.id===contractId);",
    "if(!isActive(m)||!roleCan(s,m.role,'contracts'))throw new AppError('This action is not permitted for your role.',403);const contractId=short.parse(body.contractId);const existing=s.contracts.find(x=>x.id===contractId);",
    "actions.ts: contractUpdate uses 'contracts' capability")

# rolePermissions action: Admin-only, hard-coded (this is the one action that must never be capability-gated itself)
replace_once(A,
    "if(action==='selfProfile'){",
    "if(action==='rolePermissions'){requireRole(['Admin']);const perms=body.permissions as Record<string,string[]>;if(!perms||typeof perms!=='object')throw new AppError('Invalid permissions payload.');const clean:Record<string,string[]>={};for(const roleName of roles){const caps=perms[roleName];clean[roleName]=Array.isArray(caps)?caps.filter(c=>(CAPABILITIES as readonly string[]).includes(c)):[];}s.rolePermissions=clean;event='Role permissions updated';return}if(action==='selfProfile'){",
    "actions.ts: add rolePermissions action (Admin-only, hard-coded)")

# ============================================================
# lib/context.ts: expose the current matrix so the UI can render it
# ============================================================
replace_once('lib/context.ts',
    "return {...s,tickets,members,teams:",
    "return {...s,tickets,members,rolePermissions:s.rolePermissions||{},teams:",
    "context.ts: expose rolePermissions in the client payload")

# ============================================================
# version + changelog
# ============================================================
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
- Added a configurable role-capability system: Admin can now toggle, per role, whether it can create tickets, comment, assign, escalate, archive directly, and manage contracts
- A fixed safety floor is not configurable: granting or modifying Administrator access, closing/verifying tickets, and team create/rename/delete remain hard-coded regardless of the capability matrix
- Defaults exactly match prior hard-coded behavior, so nothing changes until an Admin customizes something
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Run the frontend script (phase12b) next, then build once.")
