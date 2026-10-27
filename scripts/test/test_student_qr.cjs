const assert = require('node:assert/strict');
const { getExpoGoUrl, loadExpoManifest } = require('../dev/show-student-qr.cjs');

const address = '192.168.1.11';
const sdkMajor = require('expo/package.json').version.split('.')[0];
const manifest = { extra: { expoClient: { slug: 'MathVisionKid', hostUri: `${address}:8081`, sdkVersion: `${sdkMajor}.0.0` } } };
assert.equal(getExpoGoUrl(manifest, address), `exp://${address}:8081`);
for (const sdkVersion of [`${Number(sdkMajor) - 1}.0.0`, undefined, '']) {
  const staleManifest = { extra: { expoClient: { ...manifest.extra.expoClient, sdkVersion } } };
  assert.throws(() => getExpoGoUrl(staleManifest, address), /running Student server does not use installed Expo SDK/);
}
for (const invalidAddress of ['127.0.0.1', '127.0.0.2', '0.0.0.0', 'localhost', '::1', '']) {
  assert.throws(() => getExpoGoUrl(manifest, invalidAddress), /No usable LAN address/);
}
for (const client of [
  { slug: 'OtherProject', hostUri: `${address}:8081` },
  { slug: 'MathVisionKid', hostUri: '127.0.0.1:8081' },
  { slug: 'MathVisionKid', hostUri: `${address}:8082` },
  { slug: 'MathVisionKid', hostUri: `${address}:8081/another-path` },
]) {
  assert.throws(() => getExpoGoUrl({ extra: { expoClient: client } }, address), /MathVisionKid LAN manifest/);
}
assert.throws(() => getExpoGoUrl({}, address), /MathVisionKid LAN manifest/);
console.log('PASS: Expo Go uses the installed SDK, correct project, and LAN address; stale or mismatched manifests are rejected.');

(async () => {
  let calls = 0;
  const wait = async () => {};
  const request = async () => {
    calls++;
    if (calls === 1) throw new TypeError('fetch failed');
    if (calls === 2) return { status: 503, ok: false };
    return { status: 200, ok: true, json: async () => manifest };
  };
  assert.equal(getExpoGoUrl(await loadExpoManifest(address, request, wait), address), `exp://${address}:8081`);
  assert.equal(calls, 3);
  calls = 0;
  await assert.rejects(loadExpoManifest(address, async () => { calls++; throw new TypeError('offline'); }, wait), /offline/);
  assert.equal(calls, 3);
  calls = 0;
  await assert.rejects(loadExpoManifest(address, async () => { calls++; return { status: 401, ok: false }; }, wait), /HTTP 401/);
  assert.equal(calls, 1);
  calls = 0;
  const wrong = await loadExpoManifest(address, async () => { calls++; return { status: 200, ok: true, json: async () => ({}) }; }, wait);
  assert.throws(() => getExpoGoUrl(wrong, address), /MathVisionKid LAN manifest/);
  assert.equal(calls, 1);
  console.log('PASS: Startup retry is bounded; unavailable or wrong manifests never produce a QR.');
})().catch(error => { console.error(error); process.exitCode = 1; });
