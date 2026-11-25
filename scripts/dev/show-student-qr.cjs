const { createRequire } = require('node:module');
const { isIP } = require('node:net');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');

const mobileRoot = path.resolve(__dirname, '../../apps/student-mobile');
const { expo } = require(path.join(mobileRoot, 'app.json'));
const expoPackage = require.resolve('expo/package.json', { paths: [mobileRoot] });
const sdkMajor = require(expoPackage).version.split('.')[0];
const expoRequire = createRequire(expoPackage);
const cliRequire = createRequire(expoRequire.resolve('@expo/cli/package.json'));

function getExpoGoUrl(manifest, address, port = 8081) {
  if (isIP(address) !== 4 || address.startsWith('127.') || address === '0.0.0.0') {
    throw new Error('No usable LAN address. Connect this computer to Wi-Fi and try again.');
  }
  const client = manifest?.extra?.expoClient;
  if (client?.slug !== expo.slug || client.hostUri !== `${address}:${port}`) {
    throw new Error(`Port ${port} did not return the MathVisionKid LAN manifest. Check the Metro terminal.`);
  }
  if (typeof client.sdkVersion !== 'string' || client.sdkVersion.split('.')[0] !== sdkMajor) {
    throw new Error(`The running Student server does not use installed Expo SDK ${sdkMajor}. Close the old Student Metro terminal and restart RUN_MATHVISION.bat.`);
  }
  return `exp://${client.hostUri}`;
}

async function loadExpoManifest(address, request = fetch, wait = delay, port = 8081) {
  // The TCP listener can open before Metro is ready to serve its manifest.
  for (let attempt = 0; attempt < 3; attempt++) {
    let response;
    try {
      response = await request(`http://${address}:${port}/`, {
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
  const port = process.argv[2] === undefined ? 8081 : Number(process.argv[2]);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid Metro port.');
  const url = getExpoGoUrl(await loadExpoManifest(address, fetch, delay, port), address, port);
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
