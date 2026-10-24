/**
 * PendingPortTab.tsx — placeholder panel for tabs whose source app has not been ported yet
 * (ACC-APP-PORT-MAP / -TRIAGE / -REG / -COMMODITY). Each port replaces its placeholder with tabs/<name>/.
 * Uses the shared page template (TabHeader + EmptyState). No hex, tokens only.
 */
import { TabHeader, EmptyState, SyntheticBadge } from '../components/shared';

interface Props {
  title: string;
  question: string;
  taskCode: string;
  sourceApp: string;
  dataNote: string;
}

export function PendingPortTab({ title, question, taskCode, sourceApp, dataNote }: Props) {
  return (
    <div>
      <TabHeader title={title} question={question} badges={<SyntheticBadge label="PORT IN PROGRESS" />} />
      <EmptyState title={`${title} is being merged into this accelerator`}>
        <p>
          This tab replaces the standalone <code>{sourceApp}</code> app (tracked as <code>{taskCode}</code>).
          It will reuse the existing data sources: {dataNote}
        </p>
      </EmptyState>
    </div>
  );
}
