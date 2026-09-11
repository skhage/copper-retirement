/**
 * FilterPanel.tsx
 * Sidebar filter controls: state, risk tier, device type.
 * Drives query parameters for hex_risk_summary and device_detail.
 */
import { useMemo } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  Button,
  Skeleton,
} from '@databricks/appkit-ui/react';
import { useAnalyticsQuery } from '@databricks/appkit-ui/react';
import { USE_MOCK_DATA, getMockFilterOptions, RISK_TIERS } from '../mock/mockData';
import type { FilterOption } from '../mock/mockData';

export interface Filters {
  state: string;
  riskTier: string;
  deviceType: string;
}

interface FilterPanelProps {
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
}

export function FilterPanel({ filters, onFilterChange }: FilterPanelProps) {
  const params = useMemo(() => ({}), []);
  const { data, loading } = useAnalyticsQuery('filter_options', params, {
    autoStart: !USE_MOCK_DATA,
  });

  const options: FilterOption[] = USE_MOCK_DATA
    ? getMockFilterOptions()
    : (data as FilterOption[] | undefined) ?? [];

  const states = options.filter((o) => o.filter_type === 'state');
  const deviceTypes = options.filter((o) => o.filter_type === 'device_type');

  const handleReset = () => {
    onFilterChange({ state: 'all', riskTier: 'all', deviceType: 'all' });
  };

  if (!USE_MOCK_DATA && loading) {
    return (
      <Card className="w-64 shrink-0">
        <CardContent className="p-4 space-y-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-64 shrink-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Filters</CardTitle>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {/* State filter */}
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">State</label>
          <Select
            value={filters.state}
            onValueChange={(v) => onFilterChange({ ...filters, state: v })}
          >
            <SelectTrigger />
            <SelectContent>
              <SelectItem value="all">All States</SelectItem>
              {states.map((s) => (
                <SelectItem key={s.filter_value} value={s.filter_value}>
                  {s.filter_value} ({Number(s.device_count).toLocaleString()})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Risk tier filter */}
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Risk Tier</label>
          <Select
            value={filters.riskTier}
            onValueChange={(v) => onFilterChange({ ...filters, riskTier: v })}
          >
            <SelectTrigger />
            <SelectContent>
              <SelectItem value="all">All Tiers</SelectItem>
              {RISK_TIERS.map((tier) => (
                <SelectItem key={tier} value={tier}>
                  {tier.charAt(0).toUpperCase() + tier.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Device type filter */}
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Device Type</label>
          <Select
            value={filters.deviceType}
            onValueChange={(v) => onFilterChange({ ...filters, deviceType: v })}
          >
            <SelectTrigger />
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {deviceTypes.map((dt) => (
                <SelectItem key={dt.filter_value} value={dt.filter_value}>
                  {dt.filter_value.toUpperCase()} ({Number(dt.device_count).toLocaleString()})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button variant="outline" size="sm" onClick={handleReset} className="w-full">
          Reset Filters
        </Button>

        {USE_MOCK_DATA && (
          <p className="text-xs text-muted-foreground italic">
            Showing mock data. Real queries blocked on FIX-COORDINATES.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
