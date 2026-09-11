/**
 * smoke.spec.ts
 * Playwright smoke tests for the Dig-Safe Triage Console.
 * Validates that key UI elements render correctly with mock data.
 */
import { test, expect } from '@playwright/test';

test.describe('Dig-Safe Triage Console', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('renders heading and KPI cards', async ({ page }) => {
    await expect(page.getByText('Dig-Safe Triage Console')).toBeVisible();
    await expect(page.getByText('SYNTHETIC DATA')).toBeVisible();

    // 6 KPI cards
    await expect(page.getByText('Open Incidents')).toBeVisible();
    await expect(page.getByText('Avg Resolution')).toBeVisible();
    await expect(page.getByText('This Week')).toBeVisible();
    await expect(page.getByText('Reroutes Pending')).toBeVisible();
    await expect(page.getByText('Active Contractors')).toBeVisible();
  });

  test('renders incident map with markers', async ({ page }) => {
    await expect(page.getByText('Incident Map')).toBeVisible();
    await expect(page.getByText('incidents shown')).toBeVisible();

    // Severity legend
    await expect(page.getByText('critical')).toBeVisible();
    await expect(page.getByText('major')).toBeVisible();
    await expect(page.getByText('minor')).toBeVisible();
  });

  test('renders report incident button and form', async ({ page }) => {
    const reportBtn = page.getByText('+ Report Incident');
    await expect(reportBtn).toBeVisible();
    await reportBtn.click();

    // Form modal
    await expect(page.getByText('Report New Incident')).toBeVisible();
    await expect(page.getByText('Severity')).toBeVisible();
    await expect(page.getByText('Cable Type')).toBeVisible();
    await expect(page.getByText('Root Cause')).toBeVisible();

    // Close form
    await page.getByText('Cancel').click();
    await expect(page.getByText('Report New Incident')).not.toBeVisible();
  });

  test('tab navigation works', async ({ page }) => {
    // Default: map tab
    await expect(page.getByText('Incident Map')).toBeVisible();

    // Switch to table tab
    await page.getByRole('button', { name: 'Incident List' }).click();
    await expect(page.getByText('incidents')).toBeVisible();

    // Switch to log tab
    await page.getByRole('button', { name: 'Action Log' }).click();
    await expect(page.getByText('Action Log')).toBeVisible();
    await expect(page.getByText('actions recorded')).toBeVisible();
  });

  test('agent chat panel shows prompt when no incident selected', async ({ page }) => {
    await expect(page.getByText('Select an incident to begin analysis')).toBeVisible();
  });
});
