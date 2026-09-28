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
# lib/domain.ts: demo seed members use teams arrays
# ============================================================
D = 'lib/domain.ts'
replace_once(D, "role:'Admin',team:'Central roads',contractor:'',active:true,authUserId:owner}",
                "role:'Admin',teams:['Central roads'],contractor:'',active:true,authUserId:owner}", "seed: owner")
replace_once(D, "role:'Team lead',team:'Central roads',contractor:''}",
                "role:'Team lead',teams:['Central roads'],contractor:''}", "seed: team lead")
replace_once(D, "role:'Analyst',team:'Central roads',contractor:''}",
                "role:'Analyst',teams:['Central roads'],contractor:''}", "seed: analyst 1")
replace_once(D, "role:'Analyst',team:'East roads',contractor:''}",
                "role:'Analyst',teams:['East roads'],contractor:''}", "seed: analyst 2")
replace_once(D, "role:'Contractor',team:'',contractor:'Northline Civil (demo)'}",
                "role:'Contractor',teams:[],contractor:'Northline Civil (demo)'}", "seed: contractor")
replace_once(D, "role:'Reviewer',team:'Central roads',contractor:'',demo:true}",
                "role:'Reviewer',teams:['Central roads'],contractor:'',demo:true}", "seed: reviewer")
replace_once(D, "role:'Auditor',team:'',contractor:''}",
                "role:'Auditor',teams:[],contractor:''}", "seed: auditor")

# ============================================================
# lib/actions.ts
# ============================================================
A = 'lib/actions.ts'
replace_once(A, "if(m.role!=='Admin'&&!s.teams.includes(m.team))throw new AppError('Assign the member to a valid team first.');",
                "if(m.role!=='Admin'&&!(m.teams||[]).some(x=>s.teams.includes(x)))throw new AppError('Assign the member to a valid team first.');",
                "create ticket: member must belong to a valid team")
replace_once(A, "team:m.team||s.teams[0]||'',analyst:m.role==='Analyst'?m.id:''",
                "team:m.teams?.[0]||s.teams[0]||'',analyst:m.role==='Analyst'?m.id:''",
                "create ticket: default team is the member's first team")
replace_once(A, "(m.role==='Team lead'&&team!==m.team))throw",
                "(m.role==='Team lead'&&!m.teams.includes(team)))throw",
                "assign: Team lead must belong to the target team")
replace_once(A, "x.role==='Analyst'&&x.team===team&&isActive(x)):null;",
                "x.role==='Analyst'&&(x.teams||[]).includes(team)&&isActive(x)):null;",
                "assign: analyst must belong to the target team")
replace_once(A, "x.role==='Analyst'&&x.team===t.team&&isActive(x)",
                "x.role==='Analyst'&&(x.teams||[]).includes(t.team)&&isActive(x)",
                "transition: analyst-assigned check uses teams array")
replace_once(A, "(targetRole!=='Team lead'||x.team===t.team)",
                "(targetRole!=='Team lead'||(x.teams||[]).includes(t.team))",
                "escalate: recipients use teams array")
replace_once(A, "(x.role!=='Team lead'||x.team===t.team)",
                "(x.role!=='Team lead'||(x.teams||[]).includes(t.team))",
                "requestArchive: recipients use teams array")

# ============================================================
# app/api/detect/route.ts
# ============================================================
replace_once('app/api/detect/route.ts', "team:analyst?.team||state.teams[0]||''",
             "team:analyst?.teams?.[0]||state.teams[0]||''",
             "detect: new ticket takes the analyst's first team")

# ============================================================
# app/workspace.tsx: Roles table shows all of a member's teams
# ============================================================
replace_once('app/workspace.tsx', "<TableCell>{m.team||m.contractor||'Organization'}</TableCell>",
             "<TableCell>{(m.teams||[]).join(', ')||m.contractor||'Organization'}</TableCell>",
             "Roles table: show all teams")

# ============================================================
# tests/workflow.test.ts
# ============================================================
T = 'tests/workflow.test.ts'
replace_once(T, "s.tickets.find(t=>t.team!==lead.team)!",
                "s.tickets.find(t=>!lead.teams.includes(t.team))!", "test: team lead cannot read another team")
replace_once(T, "team:analyst.team,analyst:analyst.id}",
                "team:analyst.teams[0],analyst:analyst.id}", "test: assignment notification")
replace_once(T, "role:'Analyst',team:analyst.team,contractor:'',active:false,authUserId:uid}",
                "role:'Analyst',teams:analyst.teams,contractor:'',active:false,authUserId:uid}", "test: workload must be reassigned")
replace_once(T, "role:'Analyst',team:'Central roads',contractor:'',active:true,authUserId:'not-a-uuid'",
                "role:'Analyst',teams:['Central roads'],contractor:'',active:true,authUserId:'not-a-uuid'", "test: membership needs UUID")
replace_once(T, "role:'Analyst',team:'Central roads',contractor:'',active:false,authUserId:owner}",
                "role:'Analyst',teams:['Central roads'],contractor:'',active:false,authUserId:owner}", "test: owner cannot be demoted")
replace_once(T, "role:'Auditor',team:'',contractor:'',active:true,authUserId:crypto.randomUUID()}",
                "role:'Auditor',teams:[],contractor:'',active:true,authUserId:crypto.randomUUID()}", "test: real membership binds account")

print("\nDone. Now run:")
print("  npm run build")
