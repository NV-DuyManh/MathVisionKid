import { defineConfig, devices } from '@playwright/test';
import { sites, apiOrigin } from './tests/browser/sites.mjs';

export default defineConfig({
  testDir: './tests/browser',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  workers: 2,
  timeout: 30000,
  expect: { timeout: 10000 },
  outputDir: '.local-artifacts/browser/results',
  reporter: [['list'], ['html', { outputFolder: '.local-artifacts/browser/report', open: 'never' }]],
  use: { trace: 'retain-on-failure', screenshot: 'only-on-failure', serviceWorkers: 'block' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: Object.values(sites).map(({ workspace, port }) => ({
    command: `npm run build --workspace=${workspace} -- --outDir ../../.local-artifacts/browser/build/${workspace} && npm run preview --workspace=${workspace} -- --host 127.0.0.1 --port ${port} --strictPort --outDir ../../.local-artifacts/browser/build/${workspace}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      VITE_API_BASE_URL: `${apiOrigin}/api/v1`,
      VITE_PORTAL_URL: sites.portal.origin,
      VITE_TEACHER_URL: sites.teacher.origin,
      VITE_ADMIN_URL: sites.admin.origin,
      VITE_USE_MOCK: 'false',
      VITE_SHOW_DEV_TOOLS: 'false',
      VITE_GOOGLE_CLIENT_ID: '',
      VITE_FIREBASE_API_KEY: '',
      VITE_FIREBASE_AUTH_DOMAIN: '',
      VITE_FIREBASE_PROJECT_ID: '',
      VITE_FIREBASE_APP_ID: '',
    },
  })),
});
