/**
 * smoke.spec.ts
 * Playwright smoke tests for the Regulatory Assistant (P7-REG).
 * Demo Beat 4: "Are we clear on regs everywhere we touch?"
 *
 * Tests the 4-tab layout, KPIs, suggested questions, mock agent chat,
 * and citation sidebar — all grounded in mockData.ts (FCC 26-19 facts).
 *
 * Pattern: matches apps/copper-map/tests/smoke.spec.ts
 * @app-developer | 2026-09-11
 */
import { test, expect } from '@playwright/test';

test('app renders heading and regulatory KPIs', async ({ page }) => {
  await page.goto('/');

  // Verify heading
  await expect(
    page.getByRole('heading', { name: 'Regulatory Assistant' })
  ).toBeVisible();

  // Verify subtitle
  await expect(
    page.getByText('LakeLink Fiber — Copper Retirement Compliance')
  ).toBeVisible();

  // Verify synthetic data badge
  await expect(page.getByText('SYNTHETIC DATA')).toBeVisible();

  // Verify 6 KPI labels (from RegKPIs component, sourced from MOCK_KPIS)
  await expect(page.getByText('Jurisdictions')).toBeVisible();
  await expect(page.getByText('Pending Filings')).toBeVisible();
  await expect(page.getByText('Next Deadline')).toBeVisible();
  await expect(page.getByText('Compliance')).toBeVisible();
  await expect(page.getByText('Overdue')).toBeVisible();
  await expect(page.getByText('Documents')).toBeVisible();
});

test('four-tab navigation works', async ({ page }) => {
  await page.goto('/');

  // All four tabs visible
  await expect(page.getByRole('button', { name: 'Ask' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Jurisdiction Map' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Checklist' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Documents' })).toBeVisible();

  // Default tab is Ask — suggested questions should be visible
  await expect(page.getByText('Ask about regulatory requirements')).toBeVisible();

  // Switch to Jurisdiction Map tab
  await page.getByRole('button', { name: 'Jurisdiction Map' }).click();
  await expect(page.getByText('Colorado')).toBeVisible();
  await expect(page.getByText('Oregon')).toBeVisible();

  // Switch to Checklist tab
  await page.getByRole('button', { name: 'Checklist' }).click();
  await expect(page.getByText('Section 214')).toBeVisible();

  // Switch to Documents tab
  await page.getByRole('button', { name: 'Documents' }).click();
  await expect(page.getByText('FCC 26-19')).toBeVisible();
});

test('suggested questions are visible on Ask tab', async ({ page }) => {
  await page.goto('/');

  // All 8 suggested question chips should render (from SUGGESTED_QUESTIONS in mockData.ts)
  await expect(page.getByText('What is Section 214?')).toBeVisible();
  await expect(page.getByText('Do we still need Section 214 authorization?')).toBeVisible();
  await expect(page.getByText('What notice do we give residential customers?')).toBeVisible();
  await expect(page.getByText('What changed with FCC 26-19?')).toBeVisible();
  await expect(page.getByText("What are Colorado's requirements?")).toBeVisible();
  await expect(page.getByText('911 coordination requirements?')).toBeVisible();
  await expect(page.getByText('What are the penalties for non-compliance?')).toBeVisible();
  await expect(page.getByText('How do we handle Lifeline subscribers?')).toBeVisible();

  // Input field present
  await expect(
    page.getByPlaceholder('Ask about copper retirement regulations...')
  ).toBeVisible();
});

test('mock agent chat produces response with citations', async ({ page }) => {
  await page.goto('/');

  // Click a suggested question to trigger mock agent
  await page.getByText('What is Section 214?').click();

  // Wait for mock agent response (800ms simulated delay in RegAgentChat)
  await page.waitForTimeout(1500);

  // User message should appear
  await expect(page.getByText('What is Section 214?').last()).toBeVisible();

  // Agent response should contain Section 214(a) content
  await expect(page.getByText(/Section 214\(a\)/)).toBeVisible();
  await expect(page.getByText(/streamlined/)).toBeVisible();

  // Citation should be rendered (FCC 26-19 reference)
  await expect(page.getByText(/FCC 26-19: Accelerating Wireline/)).toBeVisible();
  await expect(page.getByText(/para\. 47-52/)).toBeVisible();

  // Suggested questions should disappear after first message sent
  await expect(page.getByText('Ask about regulatory requirements')).not.toBeVisible();
});

test('citation sidebar opens on citation click', async ({ page }) => {
  await page.goto('/');

  // Send a question to get a response with citations
  await page.getByText('What notice do we give residential customers?').click();
  await page.waitForTimeout(1500);

  // Click the citation reference (e.g. "[3] FCC 26-19...")
  // Citations render as buttons with [id] prefix
  const citationButton = page.locator('button').filter({ hasText: 'FCC 26-19: Accelerating Wireline' }).first();
  await citationButton.click();

  // Citation sidebar should open with document details
  await expect(page.getByText('Accelerating Wireline Broadband')).toBeVisible();
  await expect(page.getByText(/Federal/)).toBeVisible();

  // Sidebar should have excerpt text
  await expect(page.getByText(/90-day residential/)).toBeVisible();

  // "View full document" link should be present
  await expect(page.getByText('View full document')).toBeVisible();
});
