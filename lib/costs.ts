// Repair cost totals for Analytics and the council report.
import type {Ticket} from './domain.ts';

export type CostTotals = {tickets: number; estimate: number; actual: number; recovered: number; net: number; avgActual: number | null};
export type CostSummary = CostTotals & {
  byContractor: ({contractor: string} & CostTotals)[];
  overBudget: number; // tickets whose actual cost is more than 20% over the estimate
};

function totals(list: Ticket[]): CostTotals {
  const withCost = list.filter(t => t.cost && (t.cost.estimate !== undefined || t.cost.actual !== undefined));
  const sum = (k: 'estimate' | 'actual' | 'recovered') => withCost.reduce((a, t) => a + (t.cost?.[k] || 0), 0);
  const actuals = withCost.filter(t => t.cost?.actual !== undefined);
  const actual = sum('actual'), recovered = sum('recovered');
  return {tickets: withCost.length, estimate: sum('estimate'), actual, recovered, net: actual - recovered, avgActual: actuals.length ? Math.round(actual / actuals.length) : null};
}

export function costSummary(tickets: Ticket[]): CostSummary {
  const list = tickets.filter(t => t.status !== 'Duplicate');
  const firms = [...new Set(list.filter(t => t.cost && t.contractor).map(t => t.contractor))].sort();
  return {
    ...totals(list),
    byContractor: firms.map(contractor => ({contractor, ...totals(list.filter(t => t.contractor === contractor))})),
    overBudget: list.filter(t => t.cost?.actual !== undefined && t.cost?.estimate && t.cost.actual > t.cost.estimate * 1.2).length,
  };
}
