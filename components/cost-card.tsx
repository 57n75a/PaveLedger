'use client';
// Repair cost on a ticket: estimate, actual cost and what the contractor covers under warranty.
import {useEffect, useState} from 'react';
import {Coins} from 'lucide-react';
import {tx, useLang, locale} from '@/lib/i18n';
import {instance} from '@/lib/instance';
import {costSummary} from '@/lib/costs';
import type {Ticket} from '@/lib/domain';

const money = (n?: number | null) => n === undefined || n === null ? '—' : n.toLocaleString(locale(), {style: 'currency', currency: instance.currency, maximumFractionDigits: 0});

export function CostCard({t, canEdit, busy, mutate}: {t: Ticket; canEdit: boolean; busy: boolean; mutate: (b: Record<string, unknown>) => Promise<boolean>}) {
  useLang();
  const c = t.cost || {};
  const [est, setEst] = useState(c.estimate?.toString() ?? ''), [act, setAct] = useState(c.actual?.toString() ?? ''), [rec, setRec] = useState(c.recovered?.toString() ?? '');
  useEffect(() => { setEst(c.estimate?.toString() ?? ''); setAct(c.actual?.toString() ?? ''); setRec(c.recovered?.toString() ?? ''); }, [t.id, c.estimate, c.actual, c.recovered]);
  const warranty = !!t.contractId && t.warranty !== 'Needs review';
  const net = c.actual !== undefined ? c.actual - (c.recovered || 0) : undefined;
  const over = c.actual !== undefined && c.estimate ? Math.round((c.actual / c.estimate - 1) * 100) : null;
  return <section className="cost-card">
    <div className="cost-head"><Coins size={18}/><h3>{tx('Repair cost')}</h3>{warranty && <span className="status valid">{tx('Under warranty')}</span>}</div>
    <div className="cost-figs">
      <div><small>{tx('Estimate')}</small><b>{money(c.estimate)}</b></div>
      <div><small>{tx('Actual')}</small><b>{money(c.actual)}</b>{over !== null && over > 20 && <em className="cost-over">{tx('{0}% over estimate', [String(over)])}</em>}</div>
      <div><small>{tx('Recovered under warranty')}</small><b className="cost-good">{money(c.recovered)}</b></div>
      <div><small>{tx('Cost to the municipality')}</small><b>{money(net)}</b></div>
    </div>
    {canEdit && <form className="cost-form" onSubmit={e => { e.preventDefault(); void mutate({action: 'cost', id: t.id, estimate: est, actual: act, recovered: rec}); }}>
      <label>{tx('Estimate')} ({instance.currency})<input inputMode="numeric" value={est} onChange={e => setEst(e.target.value.replace(/[^\d]/g, ''))}/></label>
      <label>{tx('Actual')} ({instance.currency})<input inputMode="numeric" value={act} onChange={e => setAct(e.target.value.replace(/[^\d]/g, ''))}/></label>
      <label>{tx('Recovered')} ({instance.currency})<input inputMode="numeric" value={rec} onChange={e => setRec(e.target.value.replace(/[^\d]/g, ''))}/></label>
      <div className="cost-actions">
        {warranty && act && <button type="button" className="text-button" onClick={() => setRec(act)}>{tx('Contractor pays in full')}</button>}
        <button className="secondary" disabled={busy}>{tx('Save cost')}</button>
      </div>
    </form>}
  </section>;
}

export function CostPanel({tickets}: {tickets: Ticket[]}) {
  useLang();
  const s = costSummary(tickets);
  if (!s.tickets) return null;
  const share = s.actual ? Math.round(s.recovered / s.actual * 100) : 0;
  return <section className="panel cost-panel">
    <div className="section-head"><div><h2>{tx('Repair costs')}</h2><p>{tx('{0} tickets with a cost record. Amounts in {1}.', [String(s.tickets), instance.currency])}</p></div></div>
    <div className="cost-kpis">
      <div><small>{tx('Estimated')}</small><b>{money(s.estimate)}</b></div>
      <div><small>{tx('Actual')}</small><b>{money(s.actual)}</b>{s.overBudget > 0 && <em className="cost-over">{tx('{0} over budget by more than 20%', [String(s.overBudget)])}</em>}</div>
      <div><small>{tx('Recovered under warranty')}</small><b className="cost-good">{money(s.recovered)}</b><em>{tx('{0}% of actual cost', [String(share)])}</em></div>
      <div><small>{tx('Cost to the municipality')}</small><b>{money(s.net)}</b>{s.avgActual !== null && <em>{tx('Average repair {0}', [money(s.avgActual)])}</em>}</div>
    </div>
    {s.byContractor.length > 0 && <div className="cost-rows">
      {s.byContractor.map(c => <div key={c.contractor} className="cost-row">
        <span>{tx(c.contractor)}</span>
        <span className="cost-bar"><i style={{width: (c.actual ? Math.round(c.recovered / c.actual * 100) : 0) + '%'}}/></span>
        <span>{money(c.actual)}</span>
        <span className="cost-good">{money(c.recovered)}</span>
      </div>)}
      <p className="muted small">{tx('Bar: share of the actual cost recovered under warranty.')}</p>
    </div>}
  </section>;
}
