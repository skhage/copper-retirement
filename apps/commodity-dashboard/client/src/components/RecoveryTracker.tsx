/**
 * RecoveryTracker.tsx
 * Recovered copper tracking: table + scrap grade breakdown.
 * Shows volume/grade/value by decommission project.
 * Data source: copper_retirement.recovered_copper_tracking (pending P0-DATAGEN-COMMODITY-EXECUTE).
 */
import { mockRecoveryRecords, SCRAP_GRADES, USE_MOCK_DATA } from '../mock/mockData';
import type { RecoveryRecord } from '../mock/mockData';
import type { CommodityFilters } from '../App';
import { formatCurrency, formatWeight, formatDate } from '../lib/formatters';

interface Props {
  filters: CommodityFilters;
  onFilterChange: (f: CommodityFilters) => void;
}

export function RecoveryTracker({ filters, onFilterChange }: Props) {
  const records: RecoveryRecord[] = USE_MOCK_DATA ? mockRecoveryRecords : mockRecoveryRecords;

  // Apply filters
  const filtered = records.filter((r) => {
    if (filters.state !== 'all' && r.state !== filters.state) return false;
    if (filters.scrap_grade !== 'all' && r.scrap_grade !== filters.scrap_grade) return false;
    return true;
  });

  // Aggregate by grade
  const gradeAgg = Object.entries(SCRAP_GRADES).map(([key, meta]) => {
    const gradeRecords = filtered.filter((r) => r.scrap_grade === key);
    return {
      grade: key,
      label: meta.label,
      color: meta.color,
      lme_discount: meta.lme_discount_pct,
      total_lbs: gradeRecords.reduce((s, r) => s + r.weight_lbs, 0),
      total_gross: gradeRecords.reduce((s, r) => s + r.gross_value_usd, 0),
      total_net: gradeRecords.reduce((s, r) => s + r.net_value_usd, 0),
      count: gradeRecords.length,
    };
  }).filter((g) => g.count > 0);

  const totalLbs = filtered.reduce((s, r) => s + r.weight_lbs, 0);

  return (
    <div className="space-y-4">
      {/* Scrap grade filter */}
      <div className="flex gap-3 items-center">
        <label className="text-sm font-medium">Scrap Grade:</label>
        <select
          value={filters.scrap_grade}
          onChange={(e) => onFilterChange({ ...filters, scrap_grade: e.target.value })}
          className="text-sm border rounded px-2 py-1"
        >
          <option value="all">All Grades</option>
          {Object.entries(SCRAP_GRADES).map(([key, meta]) => (
            <option key={key} value={key}>{meta.label}</option>
          ))}
        </select>
        <span className="text-xs text-muted-foreground">
          {filtered.length} records | {formatWeight(totalLbs)}
        </span>
      </div>

      <div className="flex gap-4">
        {/* Grade summary cards */}
        <div className="w-[320px] flex-shrink-0 space-y-2">
          <h3 className="text-sm font-semibold">Grade Breakdown</h3>
          {gradeAgg.map((g) => (
            <div key={g.grade} className="bg-card border rounded-lg p-3 shadow-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: g.color }} />
                <span className="text-sm font-medium">{g.label}</span>
                <span className="text-xs text-muted-foreground ml-auto">{g.lme_discount} of LME</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <p className="text-muted-foreground">Weight</p>
                  <p className="font-semibold">{formatWeight(g.total_lbs)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Gross</p>
                  <p className="font-semibold">{formatCurrency(g.total_gross)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Net</p>
                  <p className="font-semibold">{formatCurrency(g.total_net)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recovery table */}
        <div className="flex-1 bg-card border rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted border-b">
                <th className="text-left px-3 py-2 text-xs font-medium">Project</th>
                <th className="text-left px-3 py-2 text-xs font-medium">Wire Center</th>
                <th className="text-left px-3 py-2 text-xs font-medium">Grade</th>
                <th className="text-right px-3 py-2 text-xs font-medium">Weight</th>
                <th className="text-right px-3 py-2 text-xs font-medium">Gross Value</th>
                <th className="text-right px-3 py-2 text-xs font-medium">Net Value</th>
                <th className="text-left px-3 py-2 text-xs font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const gradeInfo = SCRAP_GRADES[r.scrap_grade];
                return (
                  <tr key={r.recovery_id} className="border-b hover:bg-muted/50">
                    <td className="px-3 py-2 text-xs font-medium">{r.project_name}</td>
                    <td className="px-3 py-2 text-xs">{r.wire_center}</td>
                    <td className="px-3 py-2 text-xs">
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: gradeInfo?.color ?? '#6b7280' }} />
                        {gradeInfo?.label ?? r.scrap_grade}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-right">{formatWeight(r.weight_lbs)}</td>
                    <td className="px-3 py-2 text-xs text-right">{formatCurrency(r.gross_value_usd)}</td>
                    <td className="px-3 py-2 text-xs text-right">{formatCurrency(r.net_value_usd)}</td>
                    <td className="px-3 py-2 text-xs">{formatDate(r.recovery_date)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="px-3 py-2 text-xs text-muted-foreground border-t">
            {filtered.length} recovery records shown (mock — recovered_copper_tracking pending P0-DATAGEN-COMMODITY-EXECUTE)
          </div>
        </div>
      </div>
    </div>
  );
}
