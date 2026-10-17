'use client';
import {useState} from 'react';
import {RotateCcw} from 'lucide-react';
import {tx, useLang} from '@/lib/i18n';
import {instance} from '@/lib/instance';

const PACKS = [
  {id: 'serbia', label: 'Serbia: Užice and Belgrade', count: 15},
  {id: 'canada', label: 'Canada: Waterloo Region', count: 15},
] as const;

/** Admin card: load or reset a demo pack. Real sign-in accounts are kept. */
export default function DemoDataCard({mutate, busy}: {mutate: (b: any) => Promise<boolean>; busy: boolean}) {
  useLang();
  const [pack, setPack] = useState<string>(instance.demoPack);
  const chosen = PACKS.find(p => p.id === pack)!;
  return <div className="demo-card">
    <h3>{tx('Demo data')}</h3>
    <p className="footnote">{tx('Load a complete sample workspace with teams, people, contracts and tickets at every stage. Use it again after a presentation to reset the demo.')}</p>
    <div className="demo-row">
      <select aria-label={tx('Demo pack')} value={pack} onChange={e => setPack(e.target.value)} disabled={busy}>
        {PACKS.map(p => <option key={p.id} value={p.id}>{tx(p.label)}</option>)}
      </select>
      <button type="button" className="secondary" disabled={busy} onClick={async () => {
        if (!confirm(tx('Replace all tickets, contracts, teams and people with the "{0}" demo? Every user you added, and their sign-in, is removed. Only you and the workspace owner are kept. This cannot be undone.', [tx(chosen.label)]))) return;
        await mutate({action: 'loadDemo', pack});
      }}><RotateCcw size={15}/>{tx('Load demo data')}</button>
    </div>
    <p className="footnote">{tx('Demo people cannot sign in. Use Preview role at the top of the page to see the workspace as any of them.')}</p>
  </div>;
}
