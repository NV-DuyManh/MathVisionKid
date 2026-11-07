import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { validateTitle, planChecks, checkNewPaths, checkTrackedArtifacts, verifyWorkflow, checkGate } from './governance.mjs';
import { checkRegistry, routeSkills } from './skills.mjs';

test('registry resolves backend/review without unrelated UI or complexity-only review', async () => {
  const registry = await checkRegistry();
  assert.ok((await routeSkills('backend', registry)).every(s => !/ui|react|design/.test(s.id)));
  assert.ok((await routeSkills('review', registry)).some(s => s.id === 'mathvision-review'));
  await assert.rejects(routeSkills('missing-domain', registry), /Unknown domain/);
});
test('skill routes allow more than three relevant skills but still reject duplicates and unknown ids', async () => {
  const fixture = mkdtempSync(join(tmpdir(), 'mathvision-skills-'));
  const registry = { skills: ['one', 'two', 'three', 'four'].map(id => ({ id, folder: id })), routes: { complex: ['one','two','three','four'] } };
  try {
    for (const skill of registry.skills) {
      const dir = join(fixture,'.agents','skills',skill.folder);
      mkdirSync(dir,{recursive:true});
      writeFileSync(join(dir,'SKILL.md'),`---\nname: ${skill.id}\ndescription: Test skill\n---\n`);
    }
    const save = () => writeFileSync(join(fixture,'.agents','registry.json'),JSON.stringify(registry));
    save();
    assert.equal((await checkRegistry(fixture)).routes.complex.length,4);
    registry.routes.complex.push('one'); save();
    await assert.rejects(checkRegistry(fixture),/Invalid route/);
    registry.routes.complex = ['unknown']; save();
    await assert.rejects(checkRegistry(fixture),/Invalid route/);
  } finally { rmSync(fixture,{recursive:true,force:true}); }
});
test('new PR title has useful Conventional Commit text, not a cafe task requirement', () => {
  assert.equal(validateTitle('fix(voice): preserve selected voice across steps'), true);
  assert.equal(validateTitle('chore(deps): bump dependencies'), true);
  for (const title of ['Kha', 'fix: tiny', 'fix: valid description\nrun injected command']) assert.equal(validateTitle(title), false);
});
test('scope covers shared/CI changes, docs-only changes, deleted files and unusual paths', () => {
  assert.deepEqual(planChecks(['docs/engineering/naming-conventions.md', 'report/old.png']), {web:false, student:false, backend:false, ai:false,launcher:false});
  assert.equal(planChecks(['apps/student-mobile/src/a.ts']).student, true);
  assert.equal(planChecks(['apps/teacher-web/src/App.tsx']).web, true);
  assert.equal(planChecks(['ai/runtime/app/tutoring/speech_render.py']).ai, true);
  assert.equal(planChecks(['backend/business-api/src/main/a.java']).backend, true);
  assert.equal(planChecks(['scripts/dev/start-all.ps1']).launcher, true);
  for (const path of ['scripts/test/test_setup_local.ps1', 'scripts/test/test_minio_launcher_guard.ps1',
    'scripts/test/test_student_qr.cjs', 'scripts/test/test_student_metro_config.cjs', 'scripts/test/test_python_runtime_pins.py']) {
    assert.equal(planChecks([path]).launcher, true, path);
  }
  for (const path of ['DEPLOY_WEB.bat', 'scripts/start-all.bat', 'scripts/start-student-metro.ps1', 'scripts/deploy/Start-PC-Preview.ps1']) assert.equal(planChecks([path]).launcher, true);
  assert.equal(planChecks(['scripts/deploy/Start-PC-Preview.ps1']).web, true);
  for (const path of ['tests/browser/workflows.spec.mjs', 'tests/browser/fixtures.mjs', 'playwright.config.mjs']) assert.equal(planChecks([path]).web, true);
  assert.ok(Object.values(planChecks(['infra/docker/docker-compose.yml'])).every(Boolean));
  assert.ok(Object.values(planChecks(['.github/workflows/ci.yml'])).every(Boolean));
  assert.ok(Object.values(planChecks(['package-lock.json'])).every(Boolean));
  assert.ok(Object.values(planChecks([], true)).every(Boolean));
  assert.ok(Object.values(planChecks(['report/file with spaces;$(command).png'])).every(v => !v));
});
test('new secrets/artifacts are rejected but environment templates remain valid', () => {
  checkNewPaths(['.env.example', 'apps/teacher-web/.env.production.example', 'docs/setup.md']);
  for (const p of ['.env', 'apps/x/.env.local', 'demoUI/a.html', 'data/student.sqlite3', 'a/private.pem']) assert.throws(() => checkNewPaths([p]), /not allowed/);
});

test('tracked artifacts are blocked even when forced into Git; local outputs and approved receipts pass', t => {
  const fixture = mkdtempSync(join(tmpdir(), 'mathvision-hygiene-'));
  t.after(() => {
    assert.equal(dirname(resolve(fixture)), resolve(tmpdir()));
    assert.ok(basename(fixture).startsWith('mathvision-hygiene-'));
    rmSync(fixture, {recursive: true, force: true});
  });
  const git = (...args) => execFileSync('git', args, {cwd: fixture, stdio: 'pipe'});
  const write = (path, content = 'synthetic fixture\n') => {
    mkdirSync(dirname(join(fixture, path)), {recursive: true});
    writeFileSync(join(fixture, path), content);
  };
  git('init', '--quiet');
  write('.gitignore', readFileSync(new URL('../.gitignore', import.meta.url), 'utf8'));
  const approved = ['src/module.ts', 'apps/student-mobile/src/__tests__/example.test.ts',
    '.env.example', 'report/README.md', 'report/contributor-credit-20261031/verification.json',
    'reports/archive/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json'];
  for (const path of approved) write(path);
  git('add', '--', '.gitignore', ...approved);
  // Local-only files and personal Git exclusions do not change the repository policy.
  write('report/local-only/REPORT.md');
  write('coverage/local-only.json');
  write('.git/info/exclude', 'src/\n');
  write('global-ignore.txt', 'src/\n');
  git('config', 'core.excludesFile', join(fixture, 'global-ignore.txt'));
  assert.doesNotThrow(() => checkTrackedArtifacts(fixture));

  const artifacts = ['report/readded with spaces;$(command).json', 'reports/archive/old.md',
    'report/contributor-credit-20261031/unapproved.json', 'apps/student-mobile/coverage/lcov.info',
    'runtime/server.log', 'output/bundle.js', '.local-artifacts/result.json',
    'ai/runtime/app/__pycache__/cached.pyc', 'demoUI/preview.html', '.env'];
  for (const path of artifacts) write(path);
  git('add', '-f', '--', ...artifacts);
  assert.throws(() => checkTrackedArtifacts(fixture), error => {
    for (const path of artifacts) assert.ok(error.message.includes(JSON.stringify(path)));
    return true;
  });
  write('scripts/governance.mjs', readFileSync(new URL('./governance.mjs', import.meta.url), 'utf8'));
  assert.throws(() => execFileSync(process.execPath, [join(fixture, 'scripts/governance.mjs'), 'check'], {stdio: 'pipe'}), error => {
    assert.equal(error.status, 1);
    assert.ok(error.stderr.toString().includes('ignored file(s) are tracked'));
    return true;
  });
  // Unstaged deletions allow local cleanup checks; clean CI checks the committed tree.
  for (const path of artifacts) rmSync(join(fixture, path));
  assert.doesNotThrow(() => checkTrackedArtifacts(fixture));
  write('reports/archive/old.md');
  assert.throws(() => checkTrackedArtifacts(fixture), /reports\/archive\/old\.md/);
});
test('PR workflow cannot execute with privileged trigger or movable action tags', () => {
  verifyWorkflow('on:\n  pull_request:\nsteps:\n - uses: actions/checkout@' + 'a'.repeat(40));
  assert.throws(() => verifyWorkflow('on:\n  pull_request_target:\n'), /Privileged/);
  assert.throws(() => verifyWorkflow('steps:\n - uses: actions/checkout@v4'), /Pin action/);
  assert.throws(() => verifyWorkflow('run: echo ${{ github.event.pull_request.title }}'), /untrusted/);
});
test('gate never turns failure, cancellation or unexpectedly skipped checks into success', () => {
  const plan = {web:true,student:false,backend:false,ai:false,launcher:false};
  const results = {governance:'success',web:'success',student:'skipped',backend:'skipped',ai:'skipped',launcher:'skipped'};
  checkGate(results, plan);
  for (const status of ['failure','cancelled','skipped']) assert.throws(() => checkGate({...results, web:status},plan), /web/);
  assert.throws(() => checkGate({...results,governance:'failure'},plan), /Governance/);
  for (const malformed of [{}, {...plan, web: undefined}, {...plan, launcher: 'yes'}, null]) {
    assert.throws(() => checkGate(results, malformed), /plan/);
  }
  checkGate(results, {web:'true',student:'false',backend:'false',ai:'false',launcher:'false'});
});

test('main policies reserve the final PR decision to the owner without bypassing checks', () => {
  const policy = name => JSON.parse(readFileSync(new URL(`../.github/rulesets/${name}.json`, import.meta.url), 'utf8'));
  const owner = policy('main-owner-only-merge');
  const quality = policy('main-pr-and-history-protection');
  for (const rule of [owner, quality]) {
    assert.equal(rule.enforcement, 'active');
    assert.deepEqual(rule.conditions.ref_name, {include:['refs/heads/main'],exclude:[]});
  }
  assert.deepEqual(owner.rules, [{type:'update'}]);
  assert.deepEqual(owner.bypass_actors, [{actor_id:154242112,actor_type:'User',bypass_mode:'pull_request'}]);
  assert.deepEqual(quality.bypass_actors, []);
  const review = quality.rules.find(r => r.type === 'pull_request').parameters;
  assert.equal(review.required_approving_review_count, 0);
  assert.equal(review.require_extra_approval_for_unattributed_changes, false);
  assert.equal(review.dismiss_stale_reviews_on_push, true);
  assert.equal(review.required_review_thread_resolution, true);
  assert.ok(quality.rules.some(r => r.type === 'deletion'));
  assert.ok(quality.rules.some(r => r.type === 'non_fast_forward'));
  assert.deepEqual(quality.rules.find(r => r.type === 'required_status_checks').parameters.required_status_checks, [{context:'Quality gate', integration_id:15368}]);
});
