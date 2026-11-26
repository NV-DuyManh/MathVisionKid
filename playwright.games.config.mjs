import { defineConfig } from '@playwright/test';
import student from './playwright.student.config.mjs';

export default defineConfig({
  ...student,
  testMatch: ['**/game-grades.spec.mjs','**/game-catalog-layout.spec.mjs','**/consolidated-workspace.spec.mjs'],
  workers: 1,
  webServer: [student.webServer[0], student.webServer.at(-1)],
});
