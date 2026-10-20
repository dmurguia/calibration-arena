import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

test('the public benchmarks page renders the published snapshot', async ({ page }) => {
  const expected = JSON.parse(readFileSync(process.env.EXPECTED_SNAPSHOT!, 'utf8'))
  await page.goto(`${process.env.BASE_URL ?? 'https://calibrationarena.ai'}/benchmarks`)
  await expect(page.locator('[data-snapshot-id]')).toHaveAttribute('data-snapshot-id', expected.refresh.snapshot_id, { timeout: 30_000 })
  await expect(page.getByText(`Checked daily · ${expected.boards.length} model boards`, { exact: true })).toBeVisible()
  await expect(page.getByText('Last successful check', { exact: false })).toBeVisible()
  // Inspect each board, not just a successful JSON request or the page shell.
  for (const board of expected.boards) {
    await page.goto(`${process.env.BASE_URL ?? 'https://calibrationarena.ai'}/benchmarks?board=${board.benchmark_id}`)
    const name = expected.benchmarks.find((b: { id: string }) => b.id === board.benchmark_id).name
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
    const times = page.locator('.bd-freshness time')
    await expect(times.first()).toHaveAttribute('datetime', board.last_successful_check ?? board.retrieved)
    if (board.as_of) await expect(times.nth(1)).toHaveAttribute('datetime', board.as_of)
    else await expect(page.getByText('Publisher update date not provided', { exact: true })).toBeVisible()
  }
  await page.screenshot({ path: 'test-results/benchmarks-publication.png', fullPage: false })
})
