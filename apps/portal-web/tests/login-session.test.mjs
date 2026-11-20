import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';

test('Google popup returns the OAuth token and clears the Firebase session even when credentials are missing', async () => {
  const app = { name: 'mathvision-social' };
  const auth = {};
  const persistence = {};
  let initialized = false;
  let signOuts = 0;
  let hasGoogleToken = true;
  class GoogleProvider {
    static credentialFromResult() { return { idToken: hasGoogleToken ? 'google-id-token' : null }; }
  }
  const imports = {
    '@firebase/app': { getApps: () => initialized ? [app] : [], initializeApp: () => app },
    '@firebase/auth': {
      GoogleAuthProvider: GoogleProvider,
      inMemoryPersistence: persistence, browserPopupRedirectResolver: {}, getAuth: () => auth,
      initializeAuth: (value, options) => {
        assert.equal(value, app);
        assert.equal(options.persistence, persistence);
        initialized = true;
        return auth;
      },
      signInWithPopup: async (value, provider) => {
        assert.equal(value, auth);
        assert.ok(provider instanceof GoogleProvider);
        return {};
      },
      signOut: async () => { signOuts++; },
    },
    '../config/runtime': { firebaseConfig: {} },
  };
  const exports = {};
  const source = transpileModule(readFileSync(new URL('../src/services/socialAuth.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS },
  }).outputText;
  vm.runInNewContext(source, { exports, require: id => imports[id] });
  assert.equal(await exports.getGoogleCredential(), 'google-id-token');
  hasGoogleToken = false;
  await assert.rejects(exports.getGoogleCredential(), /Missing Google ID token/);
  assert.equal(signOuts, 2);
});
