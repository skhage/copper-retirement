/**
 * ContractorScorecard.tsx
 * Contractor shortlist with performance scores, safety ratings,
 * geographic assignment, and assignment capability.
 * Data source: copper_retirement.contractor_performance (pending P0-DATAGEN-CONTRACTOR-EXECUTE)
 * + tmf_businesspartner.bp_agreement (10K, available NOW).
 */
import { mockContractors, USE_MOCK_DATA } from '../mock/mockData';
import type { Contractor } from '../mock/mockData';
import type { CommodityFilters } from '../App';
import { formatCount, formatPercent, formatHours, formatOshaRate, safetyColor } from '../lib/formatters';

interface Props {
  filters: CommodityFilters;
  onFilterChange: (f: CommodityFilters) => void;
}

export function ContractorScorecard({ filters, onFilterChange }: Props) {
  const contractors: Contractor[] = USE_MOCK_DATA ? mockContractors : mockContractors;

  // Apply filters
  const filtered = contractors.filter((c) => {
    if (filters.state !== 'all' && !c.state_coverage.includes(filters.state)) return false;
    if (filters.contractor_type !== 'all' && c.type !== filters.contractor_type) return false;
    return true;
  });

  // Sort by overall rating desc
  const sorted = [...filtered].sort((a, b) => b.overall_rating - a.overall_rating);

  const contractorTypes = [...new Set(contractors.map((c) => c.type))];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-3 items-center">
        <label className="text-sm font-medium">Contractor Type:</label>
        <select
          value={filters.contractor_type}
          onChange={(e) => onFilterChange({ ...filters, contractor_type: e.target.value })}
          aria-label="Filter by contractor type"
          className="text-sm border rounded px-2 py-1 focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
        >
          <option value="all">All Types</option>
          {contractorTypes.map((t) => (
            <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <span className="text-xs text-muted-foreground">
          {sorted.length} contractors
        </span>
      </div>

      {/* Contractor cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((c) => (
          <div key={c.contractor_id} className="bg-card border rounded-lg p-4 shadow-sm">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="text-sm font-semibold">{c.name}</h4>
                <p className="text-xs text-muted-foreground capitalize">
                  {c.type.replace(/_/g, ' ')}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold">{c.overall_rating.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">/ 5.0</p>
              </div>
            </div>

            {/* Metrics grid */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
              <div>
                <p className="text-muted-foreground">Safety Score</p>
                <p className={`font-semibold ${safetyColor(c.safety_score)}`}>{c.safety_score}/100</p>
              </div>
              <div>
                <p className="text-muted-foreground">OSHA Rate</p>
                <p className="font-semibold">{formatOshaRate(c.osha_recordable_rate)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">SLA Met</p>
                <p className="font-semibold">{formatPercent(c.sla_met_pct)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Completion</p>
                <p className="font-semibold">{formatPercent(c.completion_rate_pct)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Incidents</p>
                <p className="font-semibold">{c.incident_count}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Avg Resolution</p>
                <p className="font-semibold">{formatHours(c.avg_resolution_hours)}</p>
              </div>
            </div>

            {/* Coverage + capacity */}
            <div className="flex items-center justify-between text-xs border-t pt-2">
              <div>
                <span className="text-muted-foreground">Coverage: </span>
                <span className="font-medium">{c.state_coverage.join(', ')}</span>
              </div>
              <div>
                <span className="text-muted-foreground">{c.active_projects} active / </span>
                <span className="font-medium">{formatCount(c.total_work_orders)} WOs</span>
              </div>
            </div>

            {/* Assign button */}
            <button
              aria-label={`Assign ${c.name} to project`}
              className="mt-3 w-full text-xs px-3 py-1.5 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors font-medium focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
              onClick={() => {
                if (!window.confirm(`Assign ${c.name} to project?`)) return;
                // TODO: POST /api/commodity/assign-contractor
                console.log(`[commodity-dashboard] Assign contractor ${c.contractor_id}`);
              }}
            >
              Assign to Project
            </button>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        {sorted.length} contractors shown (mock — contractor_performance pending P0-DATAGEN-CONTRACTOR-EXECUTE).
        Assignment writes to Lakebase pending P5-SCHEMA.
      </p>
    </div>
  );
}
