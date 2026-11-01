import { spawnSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const result = spawnSync(process.execPath, [resolve(root, 'node_modules/expo/bin/cli'), 'export', '--platform', 'web', '--output-dir', resolve(root, 'infra/local-runtime/admin-overhaul/student-web')], {
  cwd: resolve(root, 'apps/student-mobile'), windowsHide: true, stdio: 'inherit',
  env: { ...process.env, CI: '1', EXPO_NO_DOTENV: '1', MATHVISION_WEB_EXPORT: 'true', EXPO_PUBLIC_USE_MOCK: 'false', EXPO_PUBLIC_API_BASE_URL: 'https://overhaul-api.mathvision.example/api/v1' },
});
process.exitCode = result.status ?? 1;
