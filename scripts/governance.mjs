import { execFileSync } from 'node:child_process';
import { appendFileSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { checkPullRequestRepository } from './git-flow.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const checkNames = ['web', 'student', 'backend', 'ai', 'launcher'];
const githubFreeRunnerLimit = 20;
const isRequired = value => value === true || value === 'true';
export function validateTitle(title) {
  return /^(feat|fix|docs|test|refactor|perf|build|ci|chore|revert)(\([a-z0-9-]+\))?!?: \S.{7,}$/u.test(title) && !/[\r\n]/.test(title);
}
export function validatePullRequestLabels(labels) {
  const prLabels = JSON.parse(readFileSync(resolve(root, '.github/pr-labels.json'), 'utf8'));
  const knownPrLabels = new Set(prLabels.map(({name}) => name));
  const names = new Set(labels?.map(({name}) => name));
  const scopes = [...names].filter(name => knownPrLabels.has(name) && name.startsWith('area:'));
  const types = [...names].filter(name => knownPrLabels.has(name) && name.startsWith('type:'));
  const risks = [...names].filter(name => knownPrLabels.has(name) && name.startsWith('risk:'));
  const errors = [];
  if (types.length + Number(names.has('dependencies')) !== 1) errors.push('exactly one type:* (or dependencies)');
  if (!scopes.length) errors.push('at least one area:*');
  if (risks.length !== 1) errors.push('exactly one risk:*');
  if (errors.length) throw new Error('PR labels required: add ' + errors.join(', ') + '. See docs/engineering/git-flow.md.');
}

export function planChecks(paths, full = false) {
  const shared = full || paths.some(p => /^(?:package(?:-lock)?\.json$|\.nvmrc$|\.github\/|infra\/|scripts\/(?:governance|skills)|vendor\/|packages\/)/.test(p));
  return {
    web: shared || paths.some(p => /^apps\/(?:portal|teacher|admin)-web\/|^scripts\/deploy\/|^tests\/browser\/|^playwright\.config\.mjs$/.test(p)),
    student: shared || paths.some(p => /^apps\/student-mobile\/|^tests\/(?:student-browser\/|browser\/fixtures\.mjs$|browser\/sites\.mjs$)|^playwright(?:\.student)?\.config\.mjs$/.test(p)),
    backend: shared || paths.some(p => /^backend\/business-api\/|^scripts\/test\/test_postgres_migrations(?:_runner)?\.py$/.test(p)),
    ai: shared || paths.some(p => /^(?:ai\/runtime\/|catalog\/|contracts\/)|^scripts\/(?:ci-tutoring-requirements\.txt|test\/test_runtime_tutor_auth\.py)$/.test(p)),
    launcher: shared || paths.some(p =>
      /^scripts\/(?:dev\/|deploy\/|test\/|[^/]+\.(?:ps1|bat)$)|^[^/]+\.bat$/.test(p)
      || /^ai\/runtime\/(?:pyproject\.toml|uv\.lock|requirements(?:-lock)?\.txt)$/.test(p)),
  };
}
export function countStudentBrowserShards(plan) {
  // Governance and the gate run outside the parallel check phase.
  return isRequired(plan.student)
    ? githubFreeRunnerLimit - checkNames.filter(name => isRequired(plan[name])).length
    : 0;
}
export function checkNewPaths(paths) {
  const forbidden = paths.filter(p => /(?:^|\/)(?:node_modules|\.venv|demoUI)\/|(?:^|\/)\.env(?:$|\.)|\.(?:pem|pfx|sqlite3?|db|pt|pth|safetensors)$/i.test(p)
    && !/(?:^|\/)\.env(?:\.[a-z-]+)?\.(?:example|sample|template)$|(?:^|\/)\.env\.(?:example|sample|template)$/.test(p));
  if (forbidden.length) throw new Error(`Private/generated paths are not allowed in new changes: ${forbidden.join(', ')}`);
}
export function checkTrackedArtifacts(repositoryRoot = root) {
  // Repository ignore rules only: personal/global exclusions must not affect CI.
  const ignored = execFileSync('git', ['ls-files', '--cached', '--ignored', '--exclude-per-directory=.gitignore', '-z'], {cwd: repositoryRoot})
    .toString('utf8').split('\0').filter(Boolean)
    .filter(path => lstatSync(resolve(repositoryRoot, path), {throwIfNoEntry: false}));
  if (ignored.length) {
    throw new Error(`${ignored.length} ignored file(s) are tracked. Keep local artifacts out of Git; approved receipts need an explicit .gitignore exception:\n${ignored.slice(0, 20).map(path => JSON.stringify(path)).join('\n')}`);
  }
}
export function verifyWorkflow(source) {
  if (/pull_request_target\s*:/.test(source)) throw new Error('Privileged PR execution is not allowed');
  for (const match of source.matchAll(/^\s*-?\s*uses:\s*([^\s#]+)/gm)) {
    if (!/^[\w.-]+\/[\w./-]+@[a-f0-9]{40}$/.test(match[1])) throw new Error(`Pin action to full commit SHA: ${match[1]}`);
  }
  if (/\$\{\{\s*(?:github\.event\.pull_request\.(?:title|body)|github\.head_ref)\s*\}\}/.test(source.replace(/^\s*(?:PR_TITLE|PR_BRANCH):.*$/gm, ''))) throw new Error('Pass untrusted PR metadata through environment variables');
}
export function checkGate(results, plan) {
  if (results.governance !== 'success') throw new Error('Governance failed or was cancelled');
  for (const name of checkNames) {
    if (![true, false, 'true', 'false'].includes(plan?.[name])) throw new Error(`Missing or invalid ${name} check plan`);
    const required = isRequired(plan[name]);
    if (results[name] !== 'success' && !(results[name] === 'skipped' && !required)) throw new Error(`${name} checks did not pass`);
  }
  const shardCount = countStudentBrowserShards(plan);
  if (shardCount > 0 && String(plan.student_shards) !== String(shardCount)) {
    throw new Error(`Invalid Student browser shard plan: expected ${shardCount}`);
  }
  for (let shard = 1; shard <= shardCount; shard++) {
    const result = results[`student-browser-${shard}`];
    if (result !== 'success') {
      throw new Error(`Student browser shard ${shard}/${shardCount} did not pass (${result ?? 'missing'})`);
    }
  }
}
function changedPaths(base, filter) {
  return execFileSync('git', ['diff', ...(filter ? [`--diff-filter=${filter}`] : []), '--name-only', '-z', `${base}...HEAD`], {cwd: root}).toString('utf8').split('\0').filter(Boolean);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const command = process.argv[2] ?? 'check';
    if (command === 'check') {
      checkTrackedArtifacts();
      for (const name of readdirSync(resolve(root, '.github/workflows')).filter(n => /\.ya?ml$/.test(n))) verifyWorkflow(readFileSync(resolve(root, '.github/workflows', name), 'utf8'));
      if (process.env.GITHUB_EVENT_NAME === 'pull_request' && !validateTitle(process.env.PR_TITLE ?? '')) throw new Error('PR title: use fix(voice): describe the resulting behavior');
      if (process.env.GITHUB_EVENT_NAME === 'pull_request') {
        const event = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
        const policy = JSON.parse(readFileSync(resolve(root, '.github/git-flow.json'), 'utf8'));
        checkPullRequestRepository(event.pull_request, policy, root);
        validatePullRequestLabels(event.pull_request.labels);
      }
      if (process.env.BASE_SHA) checkNewPaths(changedPaths(process.env.BASE_SHA, 'A'));
      console.log('Governance policy checks passed. Semantic review remains a human responsibility.');
    } else if (command === 'plan') {
      const full = process.env.GITHUB_EVENT_NAME !== 'pull_request';
      const paths = full ? [] : changedPaths(process.env.BASE_SHA);
      const plan = planChecks(paths, full);
      const studentShards = countStudentBrowserShards(plan);
      for (const [key, value] of Object.entries({ ...plan, student_shards: studentShards })) {
        const line = `${key}=${value}\n`;
        if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, line);
        else process.stdout.write(line);
      }
      if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY,
        `## MathVision Review Bot\n\nPhân tích ${full ? 'toàn bộ kiểm tra' : paths.length + ' đường dẫn thay đổi'}.\n\n` +
        Object.entries(plan).map(([key, value]) => `- ${key}: ${value ? 'cần kiểm tra' : 'không bị ảnh hưởng'}`).join('\n') +
        (studentShards ? `\n- Student Playwright: ${studentShards} phần chạy song song` : '') +
        '\n\nBot chọn kiểm thử và tổng hợp kết quả; không tự review ngữ nghĩa, approve, merge hay gọi dịch vụ AI/TTS. Xem PR checklist và kết quả Quality gate.\n');
    } else if (command === 'gate') {
      const plan = JSON.parse(process.env.CHECK_PLAN);
      const needs = JSON.parse(process.env.CHECK_NEEDS);
      const results = Object.fromEntries(Object.entries(needs).map(([job, check]) => [job, check.result]));
      checkGate(results, plan);
      console.log('Required checks passed for the affected scope.');
      if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, '\n## Quality gate\n\n' + Object.entries(results).map(([key,value]) => `- ${key}: ${value}`).join('\n') + '\n');
    } else throw new Error('Usage: node scripts/governance.mjs [check|plan|gate]');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
