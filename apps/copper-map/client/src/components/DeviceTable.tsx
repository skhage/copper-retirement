/**
 * DeviceTable.tsx
 * Drill-down table showing individual copper devices in a selected
 * H3 hex cell or state. Uses DataTable in query mode when live,
 * data mode with mock data during scaffold.
 */
import { useMemo } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  DataTable,
  Badge,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { USE_MOCK_DATA, getMockDevices } from '../mock/mockData';
import type { DeviceDetailRow } from '../mock/mockData';
import type { Filters } from './FilterPanel';

interface DeviceTableProps {
  filters: Filters;
  selectedH3Cell: string | null;
}

export function DeviceTable({ filters, selectedH3Cell }: DeviceTableProps) {
  // Live query params
  const params = useMemo(
    () => ({
      h3_cell: sql.string(selectedH3Cell ?? ''),
      state_filter: sql.string(filters.state === 'all' ? '' : filters.state),
      device_type: sql.string(filters.deviceType === 'all' ? '' : filters.deviceType),
    }),
    [selectedH3Cell, filters.state, filters.deviceType]
  );

  // Mock data path
  const mockData: DeviceDetailRow[] = USE_MOCK_DATA
    ? getMockDevices(selectedH3Cell ?? undefined)
    : [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          Device Detail
          {selectedH3Cell && (
            <Badge variant="outline" className="text-xs">
              Cell: {selectedH3Cell.slice(0, 8)}…
            </Badge>
          )}
          {USE_MOCK_DATA && (
            <Badge variant="secondary" className="text-xs">Mock</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {USE_MOCK_DATA ? (
          <DataTable
            data={mockData}
            filterColumn="device_type"
            filterPlaceholder="Filter by device type…"
            pageSize={10}
            transform={(rows) =>
              (rows as DeviceDetailRow[]).map((row) => ({
                ...row,
                risk_score: `${Number(row.risk_score).toFixed(0)}`,
                latitude: Number(row.latitude).toFixed(4),
                longitude: Number(row.longitude).toFixed(4),
              }))
            }
          />
        ) : (
          <DataTable
            queryKey="device_detail"
            parameters={params}
            filterColumn="device_type"
            filterPlaceholder="Filter by device type…"
            pageSize={10}
            transform={(rows) =>
              (rows as DeviceDetailRow[]).map((row) => ({
                ...row,
                risk_score: `${Number(row.risk_score).toFixed(0)}`,
                latitude: Number(row.latitude).toFixed(4),
                longitude: Number(row.longitude).toFixed(4),
              }))
            }
          />
        )}
      </CardContent>
    </Card>
  );
}
