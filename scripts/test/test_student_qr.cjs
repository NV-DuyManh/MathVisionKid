const assert = require('node:assert/strict');
const { getExpoGoUrl } = require('../dev/show-student-qr.cjs');

const address = '192.168.1.11';
const manifest = { extra: { expoClient: { slug: 'MathVisionKid', hostUri: `${address}:8081` } } };
assert.equal(getExpoGoUrl(manifest, address), `exp://${address}:8081`);
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
console.log('PASS: Expo Go uses the correct project and LAN address; loopback and mismatched manifests are rejected.');
