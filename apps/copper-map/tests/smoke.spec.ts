/**
 * smoke.spec.ts
 * Playwright smoke tests for the Copper Retirement Impact Map.
 * REDESIGNED 2026-09-11: Tests retirement-impact framing, not device-centric.
 */
import { test, expect } from '@playwright/test';

test('app renders heading and retirement KPIs', async ({ page }) => {
  await page.goto('/');

  // Verify redesigned heading
  await expect(
    page.getByRole('heading', { name: 'Copper Retirement Impact Map' })
  ).toBeVisible();

  // Verify synthetic data badge
  await expect(page.getByText('SYNTHETIC DATA')).toBeVisible();

  // Verify retirement-focused KPIs (not device counts)
  await expect(page.getByText('Revenue at Risk')).toBeVisible();
  await expect(page.getByText('Customers on Copper')).toBeVisible();
  await expect(page.getByText('Wire Centers')).toBeVisible();
  await expect(page.getByText('Services Affected')).toBeVisible();
  await expect(page.getByText('Net Retirement Cost')).toBeVisible();
  await expect(page.getByText('Fiber Ready')).toBeVisible();
});

test('three-tab navigation works', async ({ page }) => {
  await page.goto('/');

  // All three tabs visible
  await expect(page.getByRole('button', { name: 'Impact Map' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Wire Center Table' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'What-If Analysis' })).toBeVisible();

  // Switch to table tab
  await page.getByRole('button', { name: 'Wire Center Table' }).click();
  await expect(page.getByText('Revenue MRR')).toBeVisible();
  await expect(page.getByText('Network Risk')).toBeVisible();

  // Switch to what-if tab
  await page.getByRole('button', { name: 'What-If Analysis' }).click();
  await expect(page.getByText('What-If Analysis')).toBeVisible();
  await expect(page.getByPlaceholder('Ask: What if we retire copper in...')).toBeVisible();
});

test('wire center cards show impact metrics', async ({ page }) => {
  await page.goto('/');

  // Wire center cards should show customer/revenue/network data
  await expect(page.getByText('Denver Downtown')).toBeVisible();
  await expect(page.getByText(/customers/)).toBeVisible();
  await expect(page.getByText(/MRR/)).toBeVisible();
  await expect(page.getByText(/Network:/)).toBeVisible();
  await expect(page.getByText(/Fiber:/)).toBeVisible();
});

test('impact detail panel opens on wire center click', async ({ page }) => {
  await page.goto('/');

  // Click a wire center
  await page.getByText('Denver Downtown').first().click();

  // Detail panel should show customer/revenue/network/cost breakdown
  await expect(page.getByText('Customer Impact')).toBeVisible();
  await expect(page.getByText('Revenue at Risk')).toBeVisible();
  await expect(page.getByText('Network Impact')).toBeVisible();
  await expect(page.getByText('Cost & Recovery')).toBeVisible();
  await expect(page.getByText('Constraints')).toBeVisible();

  // Shows contract-locked warning
  await expect(page.getByText(/contract-locked/)).toBeVisible();
});

test('what-if chat accepts questions and shows responses', async ({ page }) => {
  await page.goto('/');

  // Navigate to what-if tab
  await page.getByRole('button', { name: 'What-If Analysis' }).click();

  // Should show suggested questions
  await expect(page.getByText('What if we retire all copper in Colorado first?')).toBeVisible();

  // Click a suggested question
  await page.getByText('What if we retire all copper in Colorado first?').click();

  // Wait for mock agent response
  await page.waitForTimeout(1500);

  // Response should mention Colorado impact
  await expect(page.getByText(/Colorado/)).toBeVisible();
  await expect(page.getByText(/MRR/)).toBeVisible();
});

test('state filter narrows wire centers', async ({ page }) => {
  await page.goto('/');

  // Select CO state filter
  await page.locator('select').first().selectOption('CO');

  // Should show only Colorado wire centers
  await expect(page.getByText('Denver Downtown')).toBeVisible();
  await expect(page.getByText('Boulder West')).toBeVisible();

  // Non-CO wire centers should not appear
  await expect(page.getByText('Seattle Eastside')).not.toBeVisible();
  await expect(page.getByText('Portland Central')).not.toBeVisible();
});
