import { readdirSync } from 'node:fs';
import path from 'node:path';

// Exercise the installed Router against the real route filenames. Mocking push()
// would miss SDK 58 choosing a hidden camera tab and redirecting back home.
const { getRoutes } = require('expo-router/build/getRoutes');
const { getNavigationConfig } = require('expo-router/build/getLinkingConfig');
const { getStateFromPath } = require('expo-router/build/fork/getStateFromPath');
const files = readdirSync(path.resolve(__dirname, '../app'), { recursive: true })
  .filter(file => /\.[jt]sx?$/.test(String(file)))
  .map(file => './' + String(file).replace(/\\/g, '/'));
const context = Object.assign(() => ({ default: () => null }), { keys: () => files });

it.each(['android', 'ios', 'web'])('opens the root camera from every %s tab without losing lesson context', platform => {
  const routes = getRoutes(context, { platform, ignoreEntryPoints: true });
  const config = getNavigationConfig(routes, true, { sitemap: false, notFound: false });
  for (const tab of ['index', 'lessons', 'achievements', 'profile']) {
    const state = getStateFromPath('/camera?mode=MATH_TUTOR&problemText=1%2F3&retrySubmissionId=retry-1', config, ['(tabs)', tab]);
    const destination = state.routes[0].state.routes[0];
    expect(destination.name).toBe('camera');
    expect(destination.params).toEqual({ mode: 'MATH_TUTOR', problemText: '1/3', retrySubmissionId: 'retry-1' });
    expect(destination.state).toBeUndefined();
  }
});
