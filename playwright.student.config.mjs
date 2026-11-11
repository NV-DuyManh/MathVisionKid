import { defineConfig } from '@playwright/test';
import web from './playwright.config.mjs';

export default defineConfig({
  ...web,
  testDir: './tests/student-browser',
  outputDir: '.local-artifacts/student-browser/results',
  reporter: [['list'], ['html', { outputFolder: '.local-artifacts/student-browser/report', open: 'never' }]],
  webServer: [...web.webServer, {
    command: 'node tests/student-browser/server.mjs',
    url: 'http://127.0.0.1:43173/study/', reuseExistingServer: false, timeout: 180000,
  }],
});
