'use client';
// Contractor performance table for the Contracts page.
import {useMemo} from 'react';
import {tx, useLang, locale} from '@/lib/i18n';
import {contractorScorecards, REPAIR_DAYS} from '@/lib/scorecard';
import type {Ticket} from '@/lib/domain';

const pct = (v: number | null) => v === null ? '—' : Math.round(v * 100) + '%';

export default function ContractorScorecard({tickets}: {tickets: Ticket[]}) {
  useLang();
  const cards = useMemo(() => contractorScorecards(tickets, new Date().toISOString()), [tickets]);
  if (!cards.length) return null;
  return <section className="panel scorecard">
    <div className="section-head"><div>
      <h2>{tx('Contractor scorecard')}</h2>
      <p>{tx('How each firm performs on the repairs it was notified about. Repair windows from the notice: urgent {0} days, standard {1} days, low {2} days.', [String(REPAIR_DAYS.Urgent), String(REPAIR_DAYS.Standard), String(REPAIR_DAYS.Low)])}</p>
    </div></div>
    <div className="score-table" role="table" aria-label={tx('Contractor scorecard')}>
      <div className="score-row head" role="row">
        <span role="columnheader">{tx('Contractor')}</span>
        <span role="columnheader">{tx('Grade')}</span>
        <span role="columnheader">{tx('On time')}</span>
        <span role="columnheader">{tx('Fixed first time')}</span>
        <span role="columnheader">{tx('Average repair')}</span>
        <span role="columnheader">{tx('Overdue now')}</span>
        <span role="columnheader">{tx('Tickets')}</span>
      </div>
      {cards.map(c => <div className="score-row" role="row" key={c.contractor}>
        <span role="cell" className="score-name"><strong>{tx(c.contractor)}</strong><small>{tx('{0} completed · {1} open · {2} under warranty', [String(c.completed), String(c.open), String(c.warrantyCases)])}</small></span>
        <span role="cell">{c.grade ? <b className={'grade g-' + c.grade} title={tx('Score {0} of 100', [String(c.score)])}>{c.grade}</b> : <small className="muted">{tx('No completed repairs yet')}</small>}</span>
        <span role="cell"><Meter value={c.onTimeRate}/></span>
        <span role="cell"><Meter value={c.reopenRate === null ? null : 1 - c.reopenRate}/></span>
        <span role="cell">{c.avgRepairDays === null ? '—' : tx('{0} days', [c.avgRepairDays.toLocaleString(locale(), {maximumFractionDigits: 1})])}</span>
        <span role="cell" className={c.overdueOpen ? 'score-bad' : ''}>{c.overdueOpen}</span>
        <span role="cell">{c.tickets}</span>
      </div>)}
    </div>
    <p className="muted small score-note">{tx('Grade: 40% on time, 40% fixed first time (not reopened), 20% open work within its window. A from 85, B from 70, C from 55.')}</p>
  </section>;
}

function Meter({value}: {value: number | null}) {
  if (value === null) return <span className="muted">—</span>;
  const tone = value >= 0.85 ? 'good' : value >= 0.6 ? 'mid' : 'bad';
  return <span className="meter"><span className="track"><i className={tone} style={{width: Math.round(value * 100) + '%'}}/></span><em>{pct(value)}</em></span>;
}
