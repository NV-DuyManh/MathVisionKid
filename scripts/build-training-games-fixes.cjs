// Verify the released package by rebuilding its files from the pinned baseline.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'vendor/training-games');
const baseline = 'mathvisionkid-training-games-0.1.21.tgz';
const expectedHash = '5e52093cbb1b17ecfe0c8a29d88a74341ad0353b0023992b0ec8de4007836553';
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const patchName = 'defense-feedback-0.1.22.patch';
const version = '0.1.22';

function verifyPackage(stage) {
  cp.execFileSync('tar', ['-xzf', path.join(output, baseline), '-C', stage]);
  const pkg = path.join(stage, 'package');
  const patch = fs.readFileSync(path.join(output, patchName), 'utf8').replaceAll('\r\n', '\n');
  for (const [, relative] of patch.matchAll(/^\+\+\+ b\/(.+)$/gm)) {
    const target = path.resolve(pkg, relative);
    if (!target.startsWith(pkg + path.sep)) throw Error('Patch path escaped package');
    fs.writeFileSync(target, fs.readFileSync(target, 'utf8').replaceAll('\r\n', '\n'));
  }
  const patchPath = path.join(stage, 'fixes.patch');
  fs.writeFileSync(patchPath, patch);
  cp.execFileSync('git', ['apply', patchPath], {
    cwd: pkg, env: { ...process.env, GIT_CEILING_DIRECTORIES: stage },
  });
  const manifestPath = path.join(pkg, 'MANIFEST.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.version = version;
  manifest.baseline = { filename: baseline, sha256: expectedHash };
  manifest.patch = patchName;
  let changed = 0;
  for (const file of manifest.files) {
    const bytes = fs.readFileSync(path.join(pkg, file.file));
    const digest = hash(bytes);
    if (file.sha256 !== digest) changed++;
    file.bytes = bytes.length;
    file.sha256 = digest;
  }
  if (changed !== 1) throw Error(`Expected one patched source file, found ${changed}`);
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  const packagePath = path.join(pkg, 'package.json');
  const metadata = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  metadata.version = version;
  fs.writeFileSync(packagePath, JSON.stringify(metadata, null, 2) + '\n');

  const filename = `mathvisionkid-training-games-${version}.tgz`;
  const archivePath = path.join(output, filename);
  const archive = fs.readFileSync(archivePath);
  const receipt = JSON.parse(fs.readFileSync(path.join(output, 'PACKAGE_MANIFEST.json'), 'utf8'));
  const expectedReceipt = {
    name: metadata.name, version, filename,
    sha256: hash(archive), bytes: archive.length, sourceFiles: manifest.files.length,
    baseline: manifest.baseline, patch: patchName, files: manifest.files,
  };
  assert.deepEqual(receipt, expectedReceipt, 'Released package receipt differs');

  const released = path.join(stage, 'released');
  fs.mkdirSync(released);
  cp.execFileSync('tar', ['-xzf', archivePath, '-C', released]);
  cp.execFileSync('git', [
    '-c', 'core.autocrlf=false', 'diff', '--no-index', '--quiet', '--no-ext-diff', '--no-textconv',
    '--', 'package', 'released/package',
  ], { cwd: stage, env: { ...process.env, GIT_CEILING_DIRECTORIES: path.dirname(stage) } });
  console.log(`Verified ${filename} and ${manifest.files.length} source files.`);
}

if (hash(fs.readFileSync(path.join(output, baseline))) !== expectedHash) throw Error('Baseline hash mismatch');
const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'mathvision-game-fixes-'));
try {
  verifyPackage(stage);
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}
