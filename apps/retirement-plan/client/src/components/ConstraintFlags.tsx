/**
 * ConstraintFlags.tsx
 * Inline icon badges for constraint types on Gantt bars and detail panels.
 * Types: contract_locked, regulatory_notice_pending, crew_capacity_constrained,
 *        revrec_locked, none.
 */
import type { ConstraintType } from '../mock/mockData';

interface Props {
  constraint: ConstraintType;
  size?: 'sm' | 'md';
}

const CONSTRAINT_CONFIG: Record<
  ConstraintType,
  { icon: string; label: string; color: string } | null
> = {
  contract_locked: {
    icon: '\uD83D\uDD12', // lock
    label: 'Contract locked',
    color: 'bg-danger/10 text-danger',
  },
  regulatory_notice_pending: {
    icon: '\u2696\uFE0F',  // scales
    label: 'Regulatory pending',
    color: 'bg-warning/10 text-warning',
  },
  crew_capacity_constrained: {
    icon: '\uD83D\uDEE0\uFE0F', // wrench
    label: 'Crew constrained',
    color: 'bg-warning/10 text-warning',
  },
  revrec_locked: {
    icon: '\uD83D\uDCB0', // money bag
    label: 'RevRec locked',
    color: 'bg-muted text-foreground',
  },
  none: null,
};

export function ConstraintFlags({ constraint, size = 'sm' }: Props) {
  const config = CONSTRAINT_CONFIG[constraint];
  if (!config) return null;

  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1 py-0' : 'px-1.5 py-0.5';

  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded ${config.color} ${textSize} ${padding} font-medium`}
      title={config.label}
      aria-label={config.label}
      role="img"
    >
      <span>{config.icon}</span>
      {size === 'md' && <span>{config.label}</span>}
    </span>
  );
}
