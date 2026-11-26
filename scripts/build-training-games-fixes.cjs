// Rebuild the owner-requested fixes from the integrated package, without an external checkout.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'vendor/training-games');
const baseline = 'mathvisionkid-training-games-0.1.21.tgz';
const expectedHash = '5e52093cbb1b17ecfe0c8a29d88a74341ad0353b0023992b0ec8de4007836553';
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
if (hash(fs.readFileSync(path.join(output, baseline))) !== expectedHash) throw Error('Baseline hash mismatch');
const stage = fs.mkdtempSync(path.join(root, '.local-artifacts/game-fixes-build-'));
cp.execFileSync('tar', ['-xzf', path.join(output, baseline), '-C', stage]);
const pkg = path.join(stage, 'package');
const patch = fs.readFileSync(path.join(output, 'defense-feedback-0.1.22.patch'), 'utf8').replaceAll('\r\n', '\n');
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
manifest.version = '0.1.22';
manifest.baseline = { filename: baseline, sha256: expectedHash };
manifest.patch = 'defense-feedback-0.1.22.patch';
let changed = 0;
for (const file of manifest.files) {
  const bytes = fs.readFileSync(path.join(pkg, file.file));
  if (file.sha256 !== hash(bytes)) changed++;
  file.bytes = bytes.length;
  file.sha256 = hash(bytes);
}
if (changed !== 1) throw Error(`Expected one patched source file, found ${changed}`);
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
const packagePath = path.join(pkg, 'package.json');
const metadata = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
metadata.version = manifest.version;
fs.writeFileSync(packagePath, JSON.stringify(metadata, null, 2) + '\n');
const filename = `mathvisionkid-training-games-${manifest.version}.tgz`;
cp.execFileSync('tar', ['-czf', path.join(output, filename), '-C', stage, 'package']);
const archive = fs.readFileSync(path.join(output, filename));
fs.writeFileSync(path.join(output, 'PACKAGE_MANIFEST.json'), JSON.stringify({
  name: metadata.name, version: metadata.version, filename,
  sha256: hash(archive), bytes: archive.length, sourceFiles: manifest.files.length,
  baseline: manifest.baseline, patch: manifest.patch,
  files: manifest.files,
}, null, 2) + '\n');
console.log(`Built ${filename}; verified ${manifest.files.length} source files.`);
