import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateTitle, planChecks, checkNewPaths, verifyWorkflow, checkGate } from './governance.mjs';
import { checkRegistry, routeSkills } from './skills.mjs';

test('registry resolves backend/review without unrelated UI or complexity-only review', async () => {
  const registry = await checkRegistry();
  assert.ok((await routeSkills('backend', registry)).every(s => !/ui|react|design/.test(s.id)));
  assert.ok((await routeSkills('review', registry)).some(s => s.id === 'mathvision-review'));
  await assert.rejects(routeSkills('missing-domain', registry), /Unknown domain/);
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
test('PR workflow cannot execute with privileged trigger or movable action tags', () => {
  verifyWorkflow('on:\n  pull_request:\nsteps:\n - uses: actions/checkout@' + 'a'.repeat(40));
  assert.throws(() => verifyWorkflow('on:\n  pull_request_target:\n'), /Privileged/);
  assert.throws(() => verifyWorkflow('steps:\n - uses: actions/checkout@v4'), /Pin action/);
  assert.throws(() => verifyWorkflow('run: echo ${{ github.event.pull_request.title }}'), /untrusted/);
});
test('gate never turns failure, cancellation or unexpectedly skipped checks into success', () => {
  const plan = {web:true,student:false,backend:false,ai:false};
  const results = {governance:'success',web:'success',student:'skipped',backend:'skipped',ai:'skipped',launcher:'skipped'};
  checkGate(results, plan);
  for (const status of ['failure','cancelled','skipped']) assert.throws(() => checkGate({...results, web:status},plan), /web/);
  assert.throws(() => checkGate({...results,governance:'failure'},plan), /Governance/);
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
