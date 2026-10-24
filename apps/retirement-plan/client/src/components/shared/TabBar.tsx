/**
 * TabBar.tsx — WAI-ARIA tabs (BRAND_GUIDE §0, ACC-APP-UNIFY-SHELL).
 * role=tablist/tab, aria-selected, aria-controls, roving tabindex, Arrow/Home/End keys.
 * Styling comes from .ll-tabs / .ll-tab in styles/tokens.css (active = text-foreground + red underline, 44px target).
 */
import { useRef, type KeyboardEvent } from 'react';

export interface TabDef<T extends string = string> {
  id: T;
  label: string;
}

interface Props<T extends string> {
  tabs: readonly TabDef<T>[];
  activeId: T;
  onChange: (id: T) => void;
  /** Prefix for tab/panel element ids, e.g. 'top' -> tab-top-map / panel-top-map */
  idPrefix: string;
  ariaLabel: string;
}

export function tabId(prefix: string, id: string) { return `tab-${prefix}-${id}`; }
export function panelId(prefix: string, id: string) { return `panel-${prefix}-${id}`; }

export function TabBar<T extends string>({ tabs, activeId, onChange, idPrefix, ariaLabel }: Props<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const focusAt = (i: number) => {
    const n = tabs.length;
    const idx = ((i % n) + n) % n;
    refs.current[idx]?.focus();
    onChange(tabs[idx].id);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    switch (e.key) {
      case 'ArrowRight': e.preventDefault(); focusAt(i + 1); break;
      case 'ArrowLeft': e.preventDefault(); focusAt(i - 1); break;
      case 'Home': e.preventDefault(); focusAt(0); break;
      case 'End': e.preventDefault(); focusAt(tabs.length - 1); break;
    }
  };

  return (
    <nav role="tablist" aria-label={ariaLabel} className="ll-tabs px-4 md:px-6 bg-background">
      {tabs.map((t, i) => {
        const selected = t.id === activeId;
        return (
          <button
            key={t.id}
            ref={(el) => { refs.current[i] = el; }}
            id={tabId(idPrefix, t.id)}
            role="tab"
            type="button"
            aria-selected={selected}
            aria-controls={panelId(idPrefix, t.id)}
            tabIndex={selected ? 0 : -1}
            className="ll-tab"
            onClick={() => onChange(t.id)}
            onKeyDown={(e) => onKeyDown(e, i)}
          >
            {t.label}
          </button>
        );
      })}
    </nav>
  );
}
