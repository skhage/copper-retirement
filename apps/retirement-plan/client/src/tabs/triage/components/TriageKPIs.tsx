/**
 * TriageKPIs.tsx
 * Top bar showing 6 KPI cards for the dig-safe triage console.
 * Live values are an as-of replay (COO-Q-20261026-0550-3): anchored to the latest incident in the
 * SYNTHETIC table silver_dig_incident_enriched, not wall-clock today, so the cards are never all zero.
 */
import { useState, useEffect } from 'react';
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';
import type { TriageKPIs as TriageKPIsType } from '../mock/mockData';
import { fetchKPIs } from '../lib/triageApi';
import { formatCount } from '../lib/formatters';

interface KPICard {
  label: string;
  value: string;
  color: string;
  subtext?: string;
}

export function TriageKPIs() {
  const [kpis, setKpis] = useState<TriageKPIsType>(getMockKPIs());
  const [isLive, setIsLive] = useState(false);
  const [asOf, setAsOf] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(30);

  useEffect(() => {
    if (USE_MOCK_DATA) return;
    fetchKPIs()
      .then((data) => {
        setKpis(data);
        setAsOf(data.as_of ? data.as_of.slice(0, 10) : null);
        setWindowDays(data.window_days || 30);
        setIsLive(true);
      })
      .catch((err) => {
        console.warn('[TriageKPIs] Live fetch failed, using mock:', err);
      });
  }, []);

  const cards: KPICard[] = [
    {
      label: 'Open at as-of',
      value: formatCount(kpis.open_incidents),
      color: 'text-primary-strong',
      subtext: 'not yet resolved',
    },
    {
      label: 'Avg Resolution',
      value: `${kpis.avg_resolution_hours.toFixed(1)}h`,
      color: 'text-warning',
      subtext: `last ${windowDays} days`,
    },
    {
      label: 'Last 7 Days',
      value: formatCount(kpis.incidents_this_week),
      color: 'text-secondary',
      subtext: 'new incidents',
    },
    {
      label: 'Reroutes Required',
      value: formatCount(kpis.reroutes_pending),
      color: 'text-muted-foreground',
      subtext: `last ${windowDays} days`,
    },
    {
      label: 'Active Contractors',
      value: formatCount(kpis.active_contractors),
      color: 'text-accent-strong',
      subtext: 'available for dispatch',
    },
    {
      label: 'Critical',
      value: formatCount(kpis.critical_incidents),
      color: 'text-primary-strong',
      subtext: `last ${windowDays} days`,
    },
  ];

  return (
    <>
    <p className="text-xs text-muted-foreground mb-2" role="note">
      {isLive
        ? `Replay as of ${asOf ?? 'latest incident'} (synthetic incident data; windows end at the as-of date, not today).`
        : 'Sample data (live KPIs unavailable).'}
    </p>
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-card rounded-lg border p-3 shadow-sm"
        >
          <p className="text-xs text-muted-foreground mb-1">{card.label}</p>
          <p className={`text-xl font-bold ${card.color}`}>{card.value}</p>
          {card.subtext && (
            <p className="text-xs text-muted-foreground mt-1">{card.subtext}</p>
          )}
        </div>
      ))}
    </div>
    </>
  );
}
