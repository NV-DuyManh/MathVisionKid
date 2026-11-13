import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkPullRequestFlow, checkPullRequestRepository, releaseVersion } from './git-flow.mjs';
import { sourceRelease } from './git-flow-release.mjs';

const policy = JSON.parse(readFileSync(new URL('../.github/git-flow.json', import.meta.url), 'utf8'));
const pr = (head, base = 'develop', changes = {}) => ({
  number: 52, title: 'fix(flow): enforce branch routing', created_at: '2026-11-12T01:00:00Z',
  user: {login: 'contributor'},
  head: {ref: head, repo: {full_name: policy.repository}},
  base: {ref: base, repo: {full_name: policy.repository}},
  ...changes,
});

test('features and bugfixes integrate into develop, never directly into main', () => {
  for (const head of ['feature/worksheet-review','bugfix/#123_fix-reading','feature/git-flow-governance']) {
    assert.equal(checkPullRequestFlow(pr(head), policy).kind, 'task');
    assert.throws(() => checkPullRequestFlow(pr(head, 'main'), policy), /rejects/);
  }
  for (const head of ['Hieu','codex/new-task','chore/dependency-updates','feature/../main','feature/Uppercase','feature/a/b']) {
    assert.throws(() => checkPullRequestFlow(pr(head), policy), /rejects/);
  }
});

test('release and hotfix versions require valid semver and approved destinations', () => {
  for (const head of ['release/1.0.1','hotfix/1.0.2_fix-crash','hotfix/0.1.0']) {
    assert.equal(checkPullRequestFlow(pr(head, 'main'), policy).kind, 'release');
    assert.equal(checkPullRequestFlow(pr(head), policy).kind, 'backmerge');
  }
  for (const head of ['release/1','release/01.0.1','hotfix/1.0.2/extra','release/1.0.1;echo','release/1.0.1_rc']) {
    assert.equal(releaseVersion(head), null);
    assert.throws(() => checkPullRequestFlow(pr(head, 'main'), policy), /rejects/);
  }
  assert.equal(checkPullRequestFlow(pr('main'), policy).kind, 'backmerge');
  assert.throws(() => checkPullRequestFlow(pr('develop','main'), policy), /rejects/);
});

test('release stabilization accepts bugfix only and rejects feature titles', () => {
  assert.equal(checkPullRequestFlow(pr('bugfix/crash','release/1.0.1'), policy).kind, 'stabilization');
  assert.throws(() => checkPullRequestFlow(pr('feature/new-ui','release/1.0.1'), policy), /rejects/);
  assert.throws(() => checkPullRequestFlow(pr('bugfix/new-ui','release/1.0.1',{title:'feat(ui): introduce a new page'}), policy), /cannot add/);
});

test('fork tasks can be reviewed but forks cannot impersonate release/main or bot', () => {
  const fork = head => ({ref:head, repo:{full_name:'outsider/MathVisionKid'}});
  assert.equal(checkPullRequestFlow(pr('feature/real-task','develop',{head:fork('feature/real-task')}), policy).kind, 'task');
  for (const head of ['release/1.0.1','main','dependabot/npm/foo']) {
    assert.throws(() => checkPullRequestFlow(pr(head,'main',{head:fork(head)}), policy), /rejects/);
    assert.throws(() => checkPullRequestFlow(pr(head,'develop',{head:fork(head)}), policy), /rejects/);
  }
  assert.throws(() => checkPullRequestFlow(pr('dependabot/npm/foo'), policy), /rejects/);
  assert.equal(checkPullRequestFlow(pr('dependabot/npm/foo','develop',{user:{login:'dependabot[bot]'}}), policy).kind, 'task');
});

test('legacy exception is limited to the exact existing PR identity and expiry', () => {
  const legacy = policy.legacyPullRequests[0];
  const existing = pr(legacy.head, 'develop', {number:legacy.number,created_at:legacy.createdAt});
  const now = new Date('2026-11-12T12:00:00Z');
  assert.equal(checkPullRequestFlow(existing,policy,now).kind, 'task');
  for (const changed of [{number:999},{created_at:'2026-11-12T12:00:00Z'},{head:{ref:legacy.head,repo:{full_name:'outsider/fork'}}}]) {
    assert.throws(() => checkPullRequestFlow({...existing,...changed},policy,now), /rejects/);
  }
  assert.throws(() => checkPullRequestFlow(existing,policy,new Date(legacy.expiresAt)), /rejects/);
  assert.throws(() => checkPullRequestFlow({...existing,base:{...existing.base,ref:'main'}},policy,now), /rejects/);
});

test('real Git ancestry rejects stale heads even when a synthetic merge would succeed', t => {
  const fixture = mkdtempSync(join(tmpdir(), 'mathvision-git-flow-'));
  t.after(() => {
    assert.equal(dirname(resolve(fixture)), resolve(tmpdir()));
    assert.ok(basename(fixture).startsWith('mathvision-git-flow-'));
    rmSync(fixture,{recursive:true,force:true});
  });
  const git = (...args) => execFileSync('git',args,{cwd:fixture,encoding:'utf8',stdio:'pipe'}).trim();
  git('init','--quiet','-b','develop');
  git('config','user.name','Synthetic Test'); git('config','user.email','synthetic@example.invalid');
  writeFileSync(join(fixture,'initial.txt'),'initial'); git('add','.'); git('commit','-qm','chore: initial fixture');
  const initial = git('rev-parse','HEAD');
  git('switch','-qc','feature/safe-task');
  writeFileSync(join(fixture,'feature.txt'),'feature');git('add','.');git('commit','-qm','feat: synthetic task');
  const head = git('rev-parse','HEAD');
  const event = pr('feature/safe-task');event.head.sha=head;event.base.sha=initial;
  assert.doesNotThrow(() => checkPullRequestRepository(event,policy,fixture));
  git('switch','-q','develop');
  writeFileSync(join(fixture,'base.txt'),'unrelated base change');git('add','.');git('commit','-qm','fix: base update');
  event.base.sha=git('rev-parse','HEAD');
  assert.throws(() => checkPullRequestRepository(event,policy,fixture), /Update the task branch/);
  git('switch','-q','feature/safe-task');git('merge','--no-edit','develop');event.head.sha=git('rev-parse','HEAD');
  assert.doesNotThrow(() => checkPullRequestRepository(event,policy,fixture));
  event.head.ref='release/1.0.1';event.base.ref='main';
  assert.throws(() => checkPullRequestRepository(event,policy,fixture), /release notes/);
  mkdirSync(join(fixture,'docs/releases'),{recursive:true});
  writeFileSync(join(fixture,'docs/releases/1.0.1.md'),'Reviewed source release notes with validation, configuration impact, limitations and rollback guidance.\n');
  assert.doesNotThrow(() => checkPullRequestRepository(event,policy,fixture));
  event.head.ref='bugfix/new-ui';event.base.ref='release/1.0.1';event.base.sha=initial;
  assert.throws(() => checkPullRequestRepository(event,policy,fixture), /Feature commits/);
  event.head.sha='main; print secrets';
  assert.throws(() => checkPullRequestRepository(event,policy,fixture), /Invalid PR revision/);
});

test('source tags bind to actual merged release revisions and cannot tag ordinary tasks', () => {
  const sha='a'.repeat(40);
  const merged={...pr('release/1.0.1','main'),merged_at:'2026-11-12T12:00:00Z',merge_commit_sha:sha};
  const root=fileURLToPath(new URL('..',import.meta.url));
  assert.equal(sourceRelease(merged,sha,root).tag,'v1.0.1_prod');
  assert.throws(() => sourceRelease(merged,'b'.repeat(40),root), /exact merged/);
  assert.throws(() => sourceRelease({...merged,merged_at:null},sha,root), /exact merged/);
  assert.throws(() => sourceRelease({...merged,head:{ref:'feature/new-ui'}},sha,root), /exact merged/);
});
