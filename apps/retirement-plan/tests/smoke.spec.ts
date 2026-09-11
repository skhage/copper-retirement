/**
 * smoke.spec.ts
 * Playwright smoke tests for the Retirement Plan Tracker (P7-PLAN).
 * Verifies critical rendering paths with mock data.
 */
import { test, expect } from '@playwright/test';

test.describe('Retirement Plan Tracker', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('renders heading and KPI cards', async ({ page }) => {
    // Heading
    await expect(page.locator('h1')).toContainText('Retirement Plan Tracker');
    // Subtitle
    await expect(page.locator('text=LakeLink Fiber')).toBeVisible();
    // Synthetic data badge
    await expect(page.locator('text=SYNTHETIC DATA')).toBeVisible();
    // 6 KPI cards should render
    const kpiCards = page.locator('.grid-cols-6 > div');
    await expect(kpiCards).toHaveCount(6);
    // Check KPI labels
    await expect(page.locator('text=Wire Centers')).toBeVisible();
    await expect(page.locator('text=Budget Remaining')).toBeVisible();
    await expect(page.locator('text=Customers Remaining')).toBeVisible();
  });

  test('tab navigation works (Gantt, Table, Scenarios)', async ({ page }) => {
    // Default tab should be Gantt
    await expect(page.locator('text=Retirement Wave Timeline')).toBeVisible();

    // Switch to Table tab
    await page.click('text=Migration Table');
    await expect(page.locator('th:has-text("Wire Center")')).toBeVisible();
    await expect(page.locator('th:has-text("Cost")')).toBeVisible();

    // Switch to Scenarios tab
    await page.click('text=Scenario Compare');
    await expect(page.locator('text=Optimizer Scenarios')).toBeVisible();
    await expect(page.locator('text=Baseline')).toBeVisible();
  });

  test('wave filter changes Gantt content', async ({ page }) => {
    // Filter to Wave 1 only
    await page.selectOption('select >> nth=0', '1');
    // Should see fewer rows (Wave 1 has 3 wire centers in mock)
    const ganttRows = page.locator('.space-y-1 > div');
    const count = await ganttRows.count();
    expect(count).toBeLessThanOrEqual(5);
    expect(count).toBeGreaterThan(0);
  });

  test('Gantt shows wave legend with 8 waves', async ({ page }) => {
    for (let w = 1; w <= 8; w++) {
      await expect(page.locator(`text=Wave ${w}`)).toBeVisible();
    }
  });

  test('scenario cards render with cost and risk', async ({ page }) => {
    await page.click('text=Scenario Compare');
    // 3 scenario cards
    const cards = page.locator('.grid-cols-3 > div');
    await expect(cards).toHaveCount(3);
    // Active scenario should exist
    await expect(page.locator('text=active')).toBeVisible();
    // Set Active button should be present for non-active scenarios
    const setActiveButtons = page.locator('button:has-text("Set Active")');
    await expect(setActiveButtons.first()).toBeVisible();
  });
});
