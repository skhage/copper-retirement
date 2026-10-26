/**
 * formatters.ts
 * Formatting helpers for the Dig-Safe Triage Console.
 * SQL DECIMAL/BIGINT values may arrive as strings at runtime —
 * always convert before numeric operations.
 */

export const toNumber = (value: number | string | null | undefined): number =>
  Number(value ?? 0);

export const formatCount = (value: number | string): string =>
  Number(value).toLocaleString();

export const formatCurrency = (value: number | string): string =>
  `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

export const formatHours = (value: number | string | null): string => {
  if (value === null || value === undefined) return 'In progress';
  const n = Number(value);
  if (n < 1) return `${Math.round(n * 60)}m`;
  return `${n.toFixed(1)}h`;
};

export const formatPercent = (value: number | string): string =>
  `${Number(value).toFixed(1)}%`;

export const formatTimestamp = (ts: string): string => {
  const d = new Date(ts);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

export const formatDate = (dateStr: string): string => {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
};

/** Severity level → display label with icon hint */
export const severityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    critical: 'CRITICAL',
    major: 'MAJOR',
    minor: 'Minor',
    informational: 'Info',
  };
  return labels[severity] || severity;
};

/** Time since incident for "age" display */
export const incidentAge = (timestamp: string): string => {
  const ms = Date.now() - new Date(timestamp).getTime();
  const hours = ms / (1000 * 60 * 60);
  if (hours < 1) return `${Math.round(hours * 60)}m ago`;
  if (hours < 24) return `${Math.round(hours)}h ago`;
  return `${Math.round(hours / 24)}d ago`;
};
