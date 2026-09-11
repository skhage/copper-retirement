/**
 * SummaryKPIs.tsx
 * Top bar showing key metrics: total copper devices, % critical risk,
 * customers affected, wire centers remaining.
 *
 * Uses useAnalyticsQuery in live mode, mock data in scaffold mode.
 * No prebuilt KpiCard in AppKit — composed from Card + custom layout.
 */
import { useMemo } from 'react';
import { Card, CardContent, Skeleton } from '@databricks/appkit-ui/react';
import { useAnalyticsQuery } from '@databricks/appkit-ui/react';
import { formatCount, formatPercent } from '../lib/formatters';
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';
import type { MapKPIs } from '../mock/mockData';

export function SummaryKPIs() {
  const params = useMemo(() => ({}), []);
  const { data, loading, error } = useAnalyticsQuery('map_kpis', params, {
    autoStart: !USE_MOCK_DATA,
  });

  const kpis: MapKPIs | null = USE_MOCK_DATA
    ? getMockKPIs()
    : data && (data as unknown[])[0]
      ? (data as unknown[])[0] as MapKPIs
      : null;

  if (!USE_MOCK_DATA && loading) {
    return (
      <div className="grid grid-cols-5 gap-3 mb-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-3">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-8 w-1/2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!USE_MOCK_DATA && error) {
    return <div className="text-destructive mb-4">KPI load error: {String(error)}</div>;
  }

  if (!kpis) return null;

  const cards = [
    { label: 'Copper Devices', value: formatCount(kpis.total_copper_devices), sub: `CPE ${formatCount(kpis.cpe_count)} | ONT ${formatCount(kpis.ont_count)} | OLT ${formatCount(kpis.olt_count)}` },
    { label: 'Critical Risk', value: formatPercent(kpis.pct_critical_approx), sub: `${formatCount(kpis.critical_alarm_count)} critical alarms` },
    { label: 'Total Alarms', value: formatCount(kpis.total_alarms), sub: 'Across copper plant' },
    { label: 'States', value: String(kpis.states_with_copper), sub: 'With copper plant' },
    { label: 'Wire Centers', value: formatCount(kpis.wire_centers_remaining), sub: 'Remaining to retire' },
  ];

  return (
    <div className="grid grid-cols-5 gap-3 mb-4">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">{c.label}</p>
            <p className="text-2xl font-bold mt-1">{c.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{c.sub}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
