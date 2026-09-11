/**
 * DevicePopover.tsx
 * Click-on-hex detail popover showing aggregate info for a selected H3 cell.
 * Displayed as a floating card when a hex cell is clicked on the map.
 */
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@databricks/appkit-ui/react';
import { formatCount, formatRiskScore } from '../lib/formatters';
import { RISK_COLORS } from '../mock/mockData';
import type { HexRiskRow } from '../mock/mockData';

interface DevicePopoverProps {
  cell: HexRiskRow | null;
  onClose: () => void;
  onDrillDown: (cell: HexRiskRow) => void;
}

export function DevicePopover({ cell, onClose, onDrillDown }: DevicePopoverProps) {
  if (!cell) return null;

  return (
    <Card className="absolute top-4 right-4 w-72 z-50 shadow-lg">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: RISK_COLORS[cell.risk_tier] }}
          />
          <CardTitle className="text-sm">{cell.state} — Hex Cell</CardTitle>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ×
        </Button>
      </CardHeader>
      <CardContent className="p-3 space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Risk Score</span>
          <Badge
            variant={cell.risk_tier === 'critical' ? 'destructive' : 'secondary'}
          >
            {formatRiskScore(cell.avg_risk_score)}
          </Badge>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Devices</span>
          <span className="font-medium">{formatCount(cell.device_count)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Total Alarms</span>
          <span className="font-medium">{formatCount(cell.alarm_count)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Critical Alarms</span>
          <span className="font-medium text-destructive">
            {formatCount(cell.critical_alarms)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Coordinates</span>
          <span>{cell.center_lat.toFixed(2)}, {cell.center_lon.toFixed(2)}</span>
        </div>

        <Button
          variant="outline"
          size="sm"
          className="w-full mt-2"
          onClick={() => onDrillDown(cell)}
        >
          View Devices in This Cell
        </Button>
      </CardContent>
    </Card>
  );
}
