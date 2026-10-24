const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '..');
const appRoot = path.join(root, 'apps/student-mobile');
const expoCli = path.join(path.dirname(require.resolve('expo/package.json', { paths: [root] })), 'bin/cli');
const servers = JSON.parse(cp.execFileSync(process.execPath, [expoCli, 'command:ps', 'start', '--json'], { cwd: appRoot, encoding: 'utf8' }));
const samePath = (a, b) => process.platform === 'win32' ? path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase() : path.resolve(a) === path.resolve(b);
if (servers.some(server => server.alive && (samePath(server.cwd, appRoot) || samePath(server.cwd, root)))) {
  throw new Error('Stop only the MathVisionKid Expo dev server before updating packages; restart with --clear after the update.');
}
const arg = process.argv.indexOf('--source');
const source = path.resolve(arg >= 0 ? process.argv[arg + 1] : path.join(root, '../Tro_choi_cho_em'));
const builder = path.join(source, 'scripts/pack-training-games.cjs');
if (!fs.existsSync(builder)) throw new Error('Provide --source <canonical-game-repository>');
const output = path.join(root, 'vendor/training-games');
cp.execFileSync(process.execPath, [builder, '--out', output], { cwd: source, stdio: 'inherit' });
const manifest = JSON.parse(fs.readFileSync(path.join(output, 'PACKAGE_MANIFEST.json'), 'utf8'));
if (!/^[a-z0-9.-]+\.tgz$/.test(manifest.filename)) throw new Error('Unexpected package filename');
const npmSearchPaths = [path.dirname(process.execPath), path.resolve(path.dirname(process.execPath), '../lib'), ...require('node:module').globalPaths];
const npmCli = process.env.npm_execpath?.includes('npm-cli') ? process.env.npm_execpath : path.join(path.dirname(require.resolve('npm/package.json', { paths: npmSearchPaths })), 'bin/npm-cli.js');
const appManifestPath = path.join(appRoot, 'package.json');
const appManifest = JSON.parse(fs.readFileSync(appManifestPath, 'utf8'));
const lockPath = path.join(root, 'package-lock.json');
const lockedPackages = fs.existsSync(lockPath) ? JSON.parse(fs.readFileSync(lockPath, 'utf8')).packages : {};
const stale = Object.entries(lockedPackages).some(([key, value]) => key.endsWith('node_modules/' + manifest.name) && value.version !== manifest.version);
if (stale) {
  // npm 10 can retain an old file-tarball resolution after changing its spec.
  // Remove only this package through npm, preserving all other dependencies.
  cp.execFileSync(process.execPath, [npmCli, 'uninstall', manifest.name, '--workspace', 'student-mobile', '--ignore-scripts', '--no-audit', '--no-fund'], { cwd: root, stdio: 'inherit' });
}
appManifest.dependencies[manifest.name] = 'file:' + path.relative(appRoot, path.join(output, manifest.filename)).replace(/\\/g, '/');
fs.writeFileSync(appManifestPath, JSON.stringify(appManifest, null, 2) + '\n');
// Reify from the workspace root. A workspace-targeted tarball install can update
// the spec while retaining the prior file package's resolved lock entry.
cp.execFileSync(process.execPath, [npmCli, 'install', '--ignore-scripts', '--no-audit', '--no-fund'], { cwd: root, stdio: 'inherit' });
let installedRoot = path.dirname(require.resolve(manifest.name, { paths: [appRoot] }));
while (!fs.existsSync(path.join(installedRoot, 'package.json'))) installedRoot = path.dirname(installedRoot);
const installed = JSON.parse(fs.readFileSync(path.join(installedRoot, 'package.json'), 'utf8'));
if (installed.name !== manifest.name || installed.version !== manifest.version) throw new Error('Installed game package differs from the requested artifact');
console.log('Updated ' + manifest.name + '@' + manifest.version + ', SHA-256 ' + manifest.sha256);
