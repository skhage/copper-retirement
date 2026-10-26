/**
 * formatters.ts
 * Shared formatting utilities for the Retirement Plan Tracker.
 */

export function toNumber(val: unknown): number {
  if (typeof val === 'number') return val;
  if (typeof val === 'string') return parseFloat(val) || 0;
  return 0;
}

export function formatCount(n: number): string {
  return n.toLocaleString('en-US');
}

export function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export function formatPercent(n: number): string {
  return `${n.toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatQuarter(dateStr: string): string {
  const d = new Date(dateStr);
  const q = Math.ceil((d.getMonth() + 1) / 3);
  return `${d.getFullYear()} Q${q}`;
}

export function formatMonthsRemaining(endDateStr: string): string {
  const now = new Date();
  const end = new Date(endDateStr);
  const months = Math.round((end.getTime() - now.getTime()) / (30.44 * 24 * 60 * 60 * 1000));
  if (months < 0) return 'Overdue';
  if (months === 0) return 'This month';
  return `${months}mo`;
}

export function statusLabel(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
