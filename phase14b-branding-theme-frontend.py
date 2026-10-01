import pathlib, re
from datetime import date

VERSION = "2.5.2"
TODAY = date.today().isoformat()

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

WP = 'app/workspace.tsx'

# ---------- 1. Import Sun/Moon icons for the theme toggle ----------
replace_once(WP,
    "import {LayoutDashboard,ListChecks,BarChart3,Users,ShieldCheck,Bell,Plus,ArrowUpRight,Search,MapPin,Camera,CheckCircle2,RotateCcw,FileText,Truck,ExternalLink,Download,RefreshCw} from 'lucide-react';",
    "import {LayoutDashboard,ListChecks,BarChart3,Users,ShieldCheck,Bell,Plus,ArrowUpRight,Search,MapPin,Camera,CheckCircle2,RotateCcw,FileText,Truck,ExternalLink,Download,RefreshCw,Sun,Moon} from 'lucide-react';",
    "workspace.tsx: import Sun/Moon icons")

# ---------- 2. Dark-theme CSS override block, defined at module scope ----------
replace_once(WP,
    "const DEFAULT_CAPS:Record<string,string[]>={Admin:['create','comment','assign','archive','contracts'],'Team lead':['create','comment','assign','escalate','archive'],Analyst:['create','comment'],'Head Analyst':['comment','escalate'],Reviewer:['comment'],Contractor:[],Auditor:[],Vehicle:[],Director:['archive']};",
    '''const DEFAULT_CAPS:Record<string,string[]>={Admin:['create','comment','assign','archive','contracts'],'Team lead':['create','comment','assign','escalate','archive'],Analyst:['create','comment'],'Head Analyst':['comment','escalate'],Reviewer:['comment'],Contractor:[],Auditor:[],Vehicle:[],Director:['archive']};
const DARK_CSS=`[data-theme="dark"]{color-scheme:dark}[data-theme="dark"] body,[data-theme="dark"] .app-main,[data-theme="dark"] .content{background:#14161a!important;color:#e7e9ec!important}[data-theme="dark"] .panel,[data-theme="dark"] .feature-card,[data-theme="dark"] .contract,[data-theme="dark"] .panel-mini,[data-theme="dark"] .metric,[data-theme="dark"] .queue-row,[data-theme="dark"] .evidence-panel,[data-theme="dark"] .evidence-row,[data-theme="dark"] [role="dialog"]{background:#1d2026!important;color:#e7e9ec!important;border-color:#2c3038!important}[data-theme="dark"] .app-sidebar,[data-theme="dark"] .topbar{background:#15171c!important;color:#e7e9ec!important;border-color:#2c3038!important}[data-theme="dark"] input,[data-theme="dark"] select,[data-theme="dark"] textarea{background:#1d2026!important;color:#e7e9ec!important;border-color:#3a3f48!important}[data-theme="dark"] .muted,[data-theme="dark"] .footnote,[data-theme="dark"] small{color:#9aa0a8!important}[data-theme="dark"] a{color:#8ab4ff!important}[data-theme="dark"] .table-title,[data-theme="dark"] h1,[data-theme="dark"] h2,[data-theme="dark"] h3,[data-theme="dark"] strong{color:#f1f2f4!important}`;''',
    "workspace.tsx: dark-theme CSS override block")

# ---------- 3. New state: theme, brandingOpen ----------
replace_once(WP,
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null),[managingTeam,setManagingTeam]=useState<string|null>(null);",
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null),[managingTeam,setManagingTeam]=useState<string|null>(null),[theme,setTheme]=useState<'light'|'dark'>('light'),[brandingOpen,setBrandingOpen]=useState(false);",
    "workspace.tsx: add theme and brandingOpen state")

# ---------- 4. Theme persistence effects (load once, save on change) ----------
replace_once(WP,
    "async function mutate(body:any){if(!data||busy)return false;setBusy(true);try{const r=await authorizedFetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,revision:data.revision})});const d:any=await r.json();if(!r.ok){if(r.status===409)await load();throw new Error(d.error)}setData(d);toast.success('Workspace updated');return true}catch(e){toast.error((e as Error).message);return false}finally{setBusy(false)}}",
    "async function mutate(body:any){if(!data||busy)return false;setBusy(true);try{const r=await authorizedFetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,revision:data.revision})});const d:any=await r.json();if(!r.ok){if(r.status===409)await load();throw new Error(d.error)}setData(d);toast.success('Workspace updated');return true}catch(e){toast.error((e as Error).message);return false}finally{setBusy(false)}}\nuseEffect(()=>{const saved=typeof window!=='undefined'?localStorage.getItem('paveledger-theme'):null;if(saved==='dark')setTheme('dark')},[]);\nuseEffect(()=>{document.documentElement.setAttribute('data-theme',theme);localStorage.setItem('paveledger-theme',theme)},[theme]);",
    "workspace.tsx: theme load/persist effects")

# ---------- 5. Inject the dark-theme stylesheet once, at the top of the render tree ----------
replace_once(WP,
    "return <SidebarProvider><Toaster richColors/>",
    "return <SidebarProvider><style>{DARK_CSS}</style><Toaster richColors/>",
    "workspace.tsx: inject dark-theme stylesheet")

# ---------- 6. Theme toggle button in the topbar ----------
replace_once(WP,
    '<button aria-label="Refresh workspace" className="icon-btn" onClick={load}><RefreshCw size={18}/></button>',
    '<button aria-label="Toggle theme" className="icon-btn" onClick={()=>setTheme(t=>t===\'dark\'?\'light\':\'dark\')}>{theme===\'dark\'?<Sun size={18}/>:<Moon size={18}/>}</button><button aria-label="Refresh workspace" className="icon-btn" onClick={load}><RefreshCw size={18}/></button>',
    "workspace.tsx: add theme toggle button to topbar")

# ---------- 7. Sidebar logo + slogan use branding when set; Admin gets an Edit branding link ----------
replace_once(WP,
    '<a className="brand" href="/"><img src="/logo.png" alt="PaveLedger"/></a><div className="workspace-label">ROAD OPERATIONS<br/><strong>Municipal pilot workspace</strong></div>',
    '<a className="brand" href="/"><img src={data?.branding?.logoData||\'/logo.png\'} alt="PaveLedger"/></a><div className="workspace-label">ROAD OPERATIONS<br/><strong>{data?.branding?.slogan||\'Municipal pilot workspace\'}</strong>{role===\'Admin\'&&<><br/><button className="text-button" onClick={()=>setBrandingOpen(true)}>Edit branding</button></>}</div>',
    "workspace.tsx: sidebar uses branding logo/slogan, Admin edit link")

# ---------- 8. Branding edit dialog ----------
replace_once(WP,
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={brandingOpen} onOpenChange={setBrandingOpen}><DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}><DialogHeader><DialogTitle>Edit branding</DialogTitle><DialogDescription>Replace the logo and update the workspace slogan shown in the sidebar.</DialogDescription></DialogHeader><form className="form" onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const slogan=String(fd.get('slogan')||'');const file=fd.get('logo') as File;const payload:any={action:'branding',slogan};if(file&&file.size>0){if(file.size>500_000){toast.error('Logo must be under 500 KB');return}const dataUrl=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file)});payload.logoData=dataUrl;payload.logoMime=file.type}if(await mutate(payload))setBrandingOpen(false)}}><label>Slogan<input name="slogan" defaultValue={data?.branding?.slogan||'Municipal pilot workspace'} maxLength={200}/></label><label>Logo image (PNG/JPG/WebP, under 500 KB)<input name="logo" type="file" accept="image/png,image/jpeg,image/webp"/></label><button className="primary" disabled={busy}>Save branding</button></form></DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add branding edit dialog")

# ---------- version + changelog ----------
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
- Added a light/dark theme toggle in the topbar, persisted per browser
- Admin can edit the sidebar logo and slogan from a new "Edit branding" link
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
