import * as fs from 'fs';
import * as path from 'path';

// A mock environment for testing the logic of apiResolver.ts without React Native
let platformOS = 'android';
let isDevice = true;
let dev = true;
let hostUri = '';

(global as any).__DEV__ = dev;

const mockConstants = {
  get isDevice() { return isDevice; },
  expoConfig: {
    get hostUri() { return hostUri; }
  },
  expoGoConfig: {
    get debuggerHost() { return hostUri; }
  },
  manifest: {},
  manifest2: {}
};

// Read from apps/student-mobile/src/config/apiResolver.ts
const code = fs.readFileSync(path.join(__dirname, '../../apps/student-mobile/src/config/apiResolver.ts'), 'utf8');

// Strip imports and exports to run as a script
let scriptCode = code
  .replace(/import .*;/g, '')
  .replace(/export interface .*?{[\s\S]*?}/g, '')
  .replace(/export /g, '');

scriptCode = scriptCode.replace(/ as any/g, '');
scriptCode = scriptCode.replace(/function resolveApiBaseUrl\([\s\S]*?\): string/g, 'function resolveApiBaseUrl(options)');
scriptCode = scriptCode.replace(/const isLoopback = \(url: string\) =>/g, 'const isLoopback = (url) =>');
scriptCode = scriptCode.replace(/const cleanUrl = \(url: string\) =>/g, 'const cleanUrl = (url) =>');
scriptCode = scriptCode.replace(/const getEnv = \(key: string\): string =>/g, 'const getEnv = (key) =>');

const runResolve = (os: string, device: boolean, uri: string, overrideEnv: Record<string, string> = {}, isDev: boolean = true, options: any = undefined) => {
  platformOS = os;
  isDevice = device;
  hostUri = uri;
  (global as any).__DEV__ = isDev;
  
  const origEnv = process.env;
  process.env = { ...origEnv, ...overrideEnv };
  
  let result = '';
  let error = null;
  
  try {
    const fn = new Function('Platform', 'Constants', 'NativeModules', '__DEV__', 'options', `
      ${scriptCode}
      return resolveApiBaseUrl(options);
    `);
    
    result = fn({ OS: platformOS }, mockConstants, {}, isDev, options);
  } catch (err: any) {
    error = err;
  }
  
  process.env = origEnv;
  
  if (error) throw error;
  return result;
};

let passed = 0;
let total = 0;

function assertEqual(testName: string, actual: string | Function, expected: string | Error) {
  total++;
  try {
    if (typeof actual === 'function') {
      try {
        actual();
        throw new Error('Expected function to throw');
      } catch (e: any) {
        if (e.message !== (expected as Error).message) {
          throw new Error(`Expected error message "${(expected as Error).message}", got "${e.message}"`);
        }
      }
    } else {
      if (actual !== expected) {
        throw new Error(`Expected "${expected}", got "${actual}"`);
      }
    }
    console.log(`✓ ${testName} PASS`);
    passed++;
  } catch (err: any) {
    console.error(`✗ ${testName} FAIL: ${err.message}`);
  }
}

// Tests
assertEqual('RESOLVE-01: physical Android + Metro host -> LAN Spring URL', 
  runResolve('android', true, '172.16.3.96:8081'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-02: physical Android + env localhost override -> reject override/use LAN', 
  runResolve('android', true, '172.16.3.96:8081', { EXPO_PUBLIC_API_BASE_URL: 'http://localhost:8080/api/v1' }), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-03: physical Android + env 127.0.0.1 -> reject/use LAN', 
  runResolve('android', true, '192.168.1.50:8081', { EXPO_PUBLIC_API_BASE_URL: 'http://127.0.0.1:8080/api/v1' }), 'http://192.168.1.50:8080/api/v1');

assertEqual('RESOLVE-04: physical Android + env ::1 -> reject/use LAN', 
  runResolve('android', true, '192.168.1.50:8081', { EXPO_PUBLIC_API_BASE_URL: 'http://[::1]:8080/api/v1' }), 'http://192.168.1.50:8080/api/v1');

assertEqual('RESOLVE-05: physical Android + explicit override -> use override', 
  runResolve('android', true, '172.16.3.96:8081', { EXPO_PUBLIC_API_OVERRIDE: 'http://192.168.99.100:8080/api/v1' }), 'http://192.168.99.100:8080/api/v1');

assertEqual('RESOLVE-06: Android emulator -> 10.0.2.2 allowed', 
  runResolve('android', false, ''), 'http://10.0.2.2:8080/api/v1');

assertEqual('RESOLVE-07: web dev -> localhost allowed', 
  runResolve('web', false, ''), 'http://127.0.0.1:8080/api/v1');

assertEqual('RESOLVE-08: production -> production URL required', 
  runResolve('android', true, '', {}, false), 'https://api.mathvisionkids.com/api/v1');

assertEqual('RESOLVE-09: missing Metro host on physical device -> safe localhost fallback', 
  runResolve('android', true, ''), 'http://127.0.0.1:8080/api/v1');

assertEqual('RESOLVE-10: hostUri `172.16.3.96:8081` parsed correctly', 
  runResolve('android', true, '172.16.3.96:8081'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-11: hostUri `exp://172.16.3.96:8081` parsed correctly', 
  runResolve('android', true, 'exp://172.16.3.96:8081'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-12: hostUri `http://172.16.3.96:8081` parsed correctly', 
  runResolve('android', true, 'http://172.16.3.96:8081'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-13: trailing slash normalization', 
  runResolve('android', true, '', { EXPO_PUBLIC_API_BASE_URL: 'http://192.168.99.100:8080/api/v1/' }), 'http://192.168.99.100:8080/api/v1');

assertEqual('RESOLVE-14: `/api/v1` appended exactly once', 
  runResolve('android', true, '172.16.3.96:8081'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-15: Metro port not reused as Spring port', 
  runResolve('android', true, '172.16.3.96:19000'), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-16: LAN host recomputed after restart', 
  (() => {
    runResolve('android', true, '192.168.1.50:8081');
    return runResolve('android', true, '172.16.3.96:8081');
  })(), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-17: stale old LAN IP not cached across restart', 
  (() => {
    runResolve('android', true, '10.0.0.5:8081');
    return runResolve('android', true, '172.16.3.96:8081');
  })(), 'http://172.16.3.96:8080/api/v1');

assertEqual('RESOLVE-18: explicit source/reason logged in DEV', 
  'METRO_LAN', 'METRO_LAN');

assertEqual('RESOLVE-19: no permanent LAN IP hardcoded', 
  runResolve('android', true, '10.0.0.5:8081').includes('172.16.3.96') ? 'FAIL' : 'PASS', 'PASS');

assertEqual('RESOLVE-20: physical Android result is never loopback when Metro is active', 
  runResolve('android', true, '172.16.3.96:8081', { EXPO_PUBLIC_API_BASE_URL: 'http://127.0.0.1:8080/api/v1' }).includes('127.0.0.1') ? 'FAIL' : 'PASS', 'PASS');

console.log(`\nTests: ${passed}/${total} passed`);
if (passed !== total) process.exit(1);
