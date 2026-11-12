import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const task = '(?:#[1-9][0-9]*_)?[a-z0-9]+(?:[-_][a-z0-9]+)*';
const version = '(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)';
const feature = new RegExp(`^feature/${task}$`);
const bugfix = new RegExp(`^bugfix/${task}$`);
const release = new RegExp(`^release/(${version})$`);
const hotfix = new RegExp(`^hotfix/(${version})(?:_[a-z0-9]+(?:-[a-z0-9]+)*)?$`);

export function releaseVersion(branch) {
  return (branch.match(release) ?? branch.match(hotfix))?.[1] ?? null;
}

export function checkPullRequestFlow(pr, policy, now = new Date()) {
  if (!pr || !policy) throw new Error('Missing pull request or Git Flow policy');
  const head = pr.head?.ref ?? '';
  const base = pr.base?.ref ?? '';
  const sameRepository = pr.head?.repo?.full_name === policy.repository;
  if (pr.base?.repo?.full_name !== policy.repository) throw new Error('Unexpected base repository');
  const legacy = sameRepository && policy.legacyPullRequests.some(p =>
    p.number === pr.number && p.head === head && p.createdAt === pr.created_at && now < new Date(p.expiresAt));
  const dependency = sameRepository && head.startsWith('dependabot/') && pr.user?.login === 'dependabot[bot]';
  if (base === policy.integrationBranch) {
    if (feature.test(head) || bugfix.test(head) || legacy || dependency) return {kind: 'task'};
    if (sameRepository && (release.test(head) || hotfix.test(head) || head === policy.releaseBranch)) return {kind: 'backmerge'};
  } else if (base === policy.releaseBranch && sameRepository && releaseVersion(head)) {
    return {kind: 'release', version: releaseVersion(head)};
  } else if ((release.test(base) || hotfix.test(base)) && bugfix.test(head) && sameRepository) {
    if (/^feat(?:\(|!|:)/.test(pr.title ?? '')) throw new Error('Release/hotfix stabilization cannot add a feature');
    return {kind: 'stabilization'};
  }
  throw new Error(`Git Flow rejects ${head} -> ${base}. Tasks target develop; only release/<version> or hotfix/<version> target main.`);
}

export function checkPullRequestRepository(pr, policy, repositoryRoot) {
  const result = checkPullRequestFlow(pr, policy);
  const git = (...args) => execFileSync('git', args, {cwd: repositoryRoot, stdio: 'pipe'}).toString('utf8').trim();
  // Use the real PR head, not GitHub's synthetic merge, to detect stale task branches.
  if (!/^[a-f0-9]{40}$/.test(pr.base.sha) || !/^[a-f0-9]{40}$/.test(pr.head.sha)) throw new Error('Invalid PR revision');
  if (result.kind === 'task' || result.kind === 'stabilization') {
    try { git('merge-base', '--is-ancestor', pr.base.sha, pr.head.sha); }
    catch { throw new Error(`Update the task branch by merging ${pr.base.ref} before review; do not force-push shared history.`); }
  }
  if (result.kind === 'release') {
    const note = resolve(repositoryRoot, 'docs/releases', `${result.version}.md`);
    if (!existsSync(note) || readFileSync(note, 'utf8').trim().length < 80) throw new Error(`Add reviewed release notes at docs/releases/${result.version}.md`);
  }
  if (result.kind === 'stabilization') {
    const subjects = git('log', '--format=%s', `${pr.base.sha}..${pr.head.sha}`).split('\n');
    if (subjects.some(s => /^feat(?:\(|!|:)/.test(s))) throw new Error('Feature commits cannot enter a release/hotfix stabilization PR');
  }
  return result;
}
