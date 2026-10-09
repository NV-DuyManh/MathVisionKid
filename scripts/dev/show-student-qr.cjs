const { createRequire } = require('node:module');
const { isIP } = require('node:net');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');

const mobileRoot = path.resolve(__dirname, '../../apps/student-mobile');
const { expo } = require(path.join(mobileRoot, 'app.json'));
const expoRequire = createRequire(require.resolve('expo/package.json', { paths: [mobileRoot] }));
const cliRequire = createRequire(expoRequire.resolve('@expo/cli/package.json'));

function getExpoGoUrl(manifest, address) {
  if (isIP(address) !== 4 || address.startsWith('127.') || address === '0.0.0.0') {
    throw new Error('No usable LAN address. Connect this computer to Wi-Fi and try again.');
  }
  const client = manifest?.extra?.expoClient;
  if (client?.slug !== expo.slug || client.hostUri !== `${address}:8081`) {
    throw new Error('Port 8081 did not return the MathVisionKid LAN manifest. Check the Metro terminal.');
  }
  return `exp://${client.hostUri}`;
}

async function loadExpoManifest(address, request = fetch, wait = delay) {
  // The TCP listener can open before Metro is ready to serve its manifest.
  for (let attempt = 0; attempt < 3; attempt++) {
    let response;
    try {
      response = await request(`http://${address}:8081/`, {
        headers: { accept: 'application/expo+json', 'expo-platform': 'android' },
        signal: AbortSignal.timeout(15000),
      });
    } catch (error) {
      if (attempt === 2) throw error;
      await wait(2000);
      continue;
    }
    if (response.status >= 500 && attempt < 2) {
      await wait(2000);
      continue;
    }
    if (!response.ok) throw new Error(`Student Mobile manifest returned HTTP ${response.status}.`);
    return response.json();
  }
}

async function main() {
  // Reuse the same LAN selection and QR renderer as the installed Expo CLI.
  const { getIpAddressAsync } = cliRequire('./build/src/utils/ip.js');
  const { printQRCode } = cliRequire('./build/src/utils/qr.js');
  const address = process.env.REACT_NATIVE_PACKAGER_HOSTNAME?.trim() || await getIpAddressAsync();
  const url = getExpoGoUrl(await loadExpoManifest(address), address);
  console.log('\nScan with Expo Go. Keep your phone and computer on the same Wi-Fi.\n');
  printQRCode(url).print();
  console.log(`Expo Go: ${url}`);
}

if (require.main === module) {
  main().catch(error => {
    console.error(`EXPO_GO_CONNECTION_ERROR: ${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = { getExpoGoUrl, loadExpoManifest };
