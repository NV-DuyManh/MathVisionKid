import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const mode = process.argv[2] || 'admin';
const npmCli = resolve(dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js');
if (!existsSync(npmCli)) throw new Error('Cannot locate npm-cli.js beside Node.js. Run the documented npm commands directly.');
const env = {
  ...process.env,
  VITE_API_BASE_URL: 'https://api.mathvision.example/api/v1',
  VITE_PORTAL_URL: 'https://portal.mathvision.example',
  VITE_ADMIN_URL: 'https://admin.mathvision.example',
  VITE_TEACHER_URL: 'https://teacher.mathvision.example',
  VITE_USE_MOCK: 'false', VITE_SHOW_DEV_TOOLS: 'false',
  EXPO_PUBLIC_USE_MOCK: 'false',
};
const plans = {
  admin: [['run', 'test:config', '--workspace=admin-web'], ['run', 'lint', '--workspace=admin-web'], ['run', 'build', '--workspace=admin-web'], ['run', 'test:production', '--workspace=admin-web']],
  portal: [['run', 'test:config', '--workspace=portal-web'], ['run', 'lint', '--workspace=portal-web'], ['run', 'build', '--workspace=portal-web'], ['run', 'test:production', '--workspace=portal-web']],
  teacher: [['run', 'test:config', '--workspace=teacher-web'], ['run', 'lint', '--workspace=teacher-web'], ['run', 'build', '--workspace=teacher-web'], ['run', 'test:production', '--workspace=teacher-web']],
  student: [['run', 'typecheck', '--workspace=student-mobile'], ['run', 'lint', '--workspace=student-mobile'], ['test', '--workspace=student-mobile', '--', '--runInBand', '--silent', '--testTimeout=30000']],
};
plans['student-static'] = plans.student.slice(0, 2);
if (!plans[mode]) throw new Error('Use admin, portal, teacher, or student.');
const results = [];
for (const args of plans[mode]) {
  console.log('RUN npm ' + args.join(' '));
  const result = spawnSync(process.execPath, [npmCli, ...args], { cwd: root, env, encoding: 'utf8', maxBuffer: 20 * 1024 * 1024, windowsHide: true });
  const output = (result.stdout || '') + (result.stderr || '');
  console.log(output);
  results.push({ command: 'npm ' + args.join(' '), exitCode: result.status, output });
  if (result.error) results[results.length - 1].error = result.error.message;
}
const directory = resolve(root, 'infra/local-runtime/admin-overhaul');
mkdirSync(directory, { recursive: true });
writeFileSync(resolve(directory, mode + '-checks.json'), JSON.stringify(results, null, 2));
process.exitCode = results.some(result => result.exitCode !== 0) ? 1 : 0;
