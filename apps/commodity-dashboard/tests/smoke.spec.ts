/**
 * smoke.spec.ts
 * Playwright smoke tests for the Commodity & Workforce Dashboard.
 * Validates that key UI elements render correctly with mock data.
 */
import { test, expect } from '@playwright/test';

test.describe('Commodity & Workforce Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('renders heading and KPI cards', async ({ page }) => {
    await expect(page.getByText('Commodity & Workforce Dashboard')).toBeVisible();
    await expect(page.getByText('SYNTHETIC DATA')).toBeVisible();

    // Key KPI cards
    await expect(page.getByText('Copper Spot')).toBeVisible();
    await expect(page.getByText('Recovered Copper')).toBeVisible();
    await expect(page.getByText('Net Recovery')).toBeVisible();
    await expect(page.getByText('Active Contractors')).toBeVisible();
    await expect(page.getByText('Decom Projects')).toBeVisible();
  });

  test('renders price chart and recommendation on forecast tab', async ({ page }) => {
    // Default tab is forecast
    await expect(page.getByText('Copper Price History & Forecast')).toBeVisible();
    await expect(page.getByText('LME Spot')).toBeVisible();
    await expect(page.getByText('AI Recommendation')).toBeVisible();
    await expect(page.getByText('SELL')).toBeVisible();
    await expect(page.getByText('FX Context')).toBeVisible();
  });

  test('tab navigation works', async ({ page }) => {
    // Default: forecast tab
    await expect(page.getByText('Copper Price History & Forecast')).toBeVisible();

    // Switch to recovery tab
    await page.getByRole('button', { name: 'Recovery Tracker' }).click();
    await expect(page.getByText('Grade Breakdown')).toBeVisible();
    await expect(page.getByText('recovery records')).toBeVisible();

    // Switch to contractors tab
    await page.getByRole('button', { name: 'Contractors' }).click();
    await expect(page.getByText('contractors')).toBeVisible();
    await expect(page.getByText('Assign to Project')).toBeVisible();
  });

  test('state filter dropdown is present', async ({ page }) => {
    const select = page.getByRole('combobox').first();
    await expect(select).toBeVisible();
    // Should have all LEGACY_STATES + 'All States'
    await expect(page.getByText('All States')).toBeVisible();
  });

  test('scrap grade filter works on recovery tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Recovery Tracker' }).click();
    await expect(page.getByText('Scrap Grade')).toBeVisible();
    await expect(page.getByText('Bare Bright')).toBeVisible();
  });
});
