'use client';
import {Check, ArrowRight, PauseCircle, RotateCcw, XCircle, Copy, Clock} from 'lucide-react';
import {tx, useLang, locale} from '@/lib/i18n';
import {colors, type Ticket, type Member} from '@/lib/domain';
import {ticketFlow, nextStep, PHASES} from '@/lib/workflow';

const FLAG_TEXT: Record<string, {text: string; icon: any; tone: string}> = {
  'reopened': {text: 'Reopened: the earlier repair did not hold. The ticket is back in investigation.', icon: RotateCcw, tone: 'warn'},
  'on-hold': {text: 'On hold: work is paused at this step.', icon: PauseCircle, tone: 'muted'},
  'rejected': {text: 'Rejected: the ticket ended here without a repair.', icon: XCircle, tone: 'muted'},
  'duplicate': {text: 'Duplicate: the work continues on the primary ticket.', icon: Copy, tone: 'muted'},
  'pending-closure': {text: 'Pending closure: a vehicle pass found the road clear. It closes automatically unless the team objects.', icon: Clock, tone: 'ok'},
};

const shortDate = (iso?: string) => iso ? new Date(iso).toLocaleDateString(locale(), {day: 'numeric', month: 'short'}) : '';

/** Seven-phase stepper from report to closure. */
export function TicketStepper({ticket}: {ticket: Ticket}) {
  useLang();
  const flow = ticketFlow(ticket);
  const flag = flow.flag ? FLAG_TEXT[flow.flag] : null;
  const accent = colors[ticket.status] || '#365cbf';
  return <section className="flow" aria-label={tx('Ticket progress')}>
    <ol className="flow-steps">
      {flow.steps.map((s, i) => {
        const halted = flow.ended && ticket.status !== 'Verified closed' && i >= flow.current;
        return <li key={s.phase.key} className={'flow-step ' + s.state + (halted ? ' halted' : '')} aria-current={s.state === 'current' ? 'step' : undefined}>
          <span className="flow-dot" style={s.state === 'current' ? {background: accent, borderColor: accent} : undefined}>
            {s.state === 'done' ? <Check size={13} strokeWidth={3}/> : <b>{i + 1}</b>}
          </span>
          {i < flow.steps.length - 1 && <span className="flow-line"/>}
          <span className="flow-label">{tx(s.phase.label)}</span>
          <span className="flow-sub">{s.state === 'skipped' ? tx('Skipped') : s.state === 'current' ? tx(s.status || ticket.status) : shortDate(s.at)}</span>
        </li>;
      })}
    </ol>
    {flag && <p className={'flow-flag ' + flag.tone}><flag.icon size={16}/>{tx(flag.text)}</p>}
  </section>;
}

/** What should happen next on this ticket, who does it, and a button when it is the viewer's turn. */
export function NextStepCard({ticket, viewer, onAct}: {ticket: Ticket; viewer: Member; onAct: (target: 'assignment' | 'stage' | 'evidence', stage?: string) => void}) {
  useLang();
  const n = nextStep(ticket, viewer);
  if (!n.text) return null;
  const done = !n.who;
  // The step is the viewer's own when their role is the one expected to act; admins can still act on others' behalf.
  const ownStep = n.mine && (n.who === viewer.role || (n.who === 'Analyst' && ticket.analyst === viewer.id));
  return <div className={'next-step' + (ownStep ? ' mine' : '') + (done ? ' done' : '')}>
    <div className="next-step-head">
      <span className="next-step-eyebrow">{done ? tx('Status') : n.mine && ownStep ? tx('Your next step') : tx('Next step')}</span>
      {n.who && !ownStep && <span className="next-step-who">{tx('Waiting on: {0}', [tx(n.who)])}</span>}
    </div>
    <p>{tx(n.text)}</p>
    {n.mine && n.target && <button className="primary" onClick={() => onAct(n.target!, n.stage)}>
      {n.target === 'assignment' ? tx('Open assignment') : ownStep ? tx('Move to: {0}', [tx(n.stage || '')]) : tx('Record on their behalf: {0}', [tx(n.stage || '')])}<ArrowRight size={16}/>
    </button>}
  </div>;
}

/** Compact seven-segment progress bar for table rows. */
export function FlowBar({ticket}: {ticket: Ticket}) {
  useLang();
  const flow = ticketFlow(ticket);
  const color = ['Rejected', 'Duplicate'].includes(ticket.status) ? '#9aa3af' : colors[ticket.status] || '#365cbf';
  const reached = ticket.status === 'Verified closed' ? PHASES.length : flow.current + 1;
  const label = tx('Step {0} of {1}: {2}', [Math.min(reached, PHASES.length), PHASES.length, tx(PHASES[Math.min(flow.current, PHASES.length - 1)].label)]);
  return <span className="flow-bar" role="img" aria-label={label} title={label}>
    {PHASES.map((p, i) => <i key={p.key} style={i < reached ? {background: color} : undefined}/>)}
  </span>;
}
