import { defineConfig } from '@playwright/test';
import web from './playwright.config.mjs';
import { studentPort } from './tests/browser/sites.mjs';

export default defineConfig({
  ...web,
  testDir: './tests/student-browser',
  outputDir: '.local-artifacts/student-browser/results',
  reporter: [['list'], ['html', { outputFolder: '.local-artifacts/student-browser/report', open: 'never' }]],
  webServer: [...web.webServer, {
    command: 'node tests/student-browser/server.mjs',
    url: `http://127.0.0.1:${studentPort}/study/`, reuseExistingServer: false, timeout: 180000,
  }],
});
