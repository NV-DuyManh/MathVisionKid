import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { releaseVersion } from './git-flow.mjs';

export function sourceRelease(pr, sha, repositoryRoot) {
  const version = releaseVersion(pr.head?.ref ?? '');
  if (!version || !pr.merged_at || pr.base?.ref !== 'main' || pr.merge_commit_sha !== sha) throw new Error('Release must point to the exact merged release/hotfix PR revision');
  const notesFile = resolve(repositoryRoot, 'docs/releases', `${version}.md`);
  if (readFileSync(notesFile, 'utf8').trim().length < 80) throw new Error('Release notes are missing or empty');
  return {tag: `v${version}_prod`, notesFile};
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const sha = process.env.GITHUB_SHA;
    const repo = process.env.GITHUB_REPOSITORY;
    if (process.env.GITHUB_EVENT_NAME !== 'push' || process.env.GITHUB_REF !== 'refs/heads/main' || repo !== 'NV-DuyManh/MathVisionKid' || !/^[a-f0-9]{40}$/.test(sha ?? '')) throw new Error('Source release is restricted to a successful main push');
    const gh = (...args) => execFileSync('gh', args, {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']}).trim();
    const prs = JSON.parse(gh('api', `repos/${repo}/commits/${sha}/pulls`));
    const pr = prs.find(p => p.merge_commit_sha === sha && p.base.ref === 'main' && p.merged_at && releaseVersion(p.head.ref));
    if (!pr) throw new Error('No merged release/hotfix PR for this main revision');
    const result = sourceRelease(pr, sha, process.cwd());
    const tags = JSON.parse(gh('api', `repos/${repo}/git/matching-refs/tags/${result.tag}`));
    const existing = tags.find(t => t.ref === `refs/tags/${result.tag}`);
    if (existing) {
      const target = existing.object.type === 'tag' ? JSON.parse(gh('api', `repos/${repo}/git/tags/${existing.object.sha}`)).object.sha : existing.object.sha;
      if (target !== sha) throw new Error('Existing release tag points to another revision; never move published tags');
      gh('release', 'view', result.tag, '--repo', repo);
      console.log(`Source release already exists: ${result.tag}`);
    } else {
      gh('release', 'create', result.tag, '--repo', repo, '--target', sha, '--title', `MathVisionKid ${result.tag} (source)`, '--notes-file', result.notesFile);
      console.log(`Published source release: ${result.tag}`);
    }
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
