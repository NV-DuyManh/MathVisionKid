import { transformSync } from '@babel/core';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

it('preserves the configured API address in an Android bundle without runtime environment variables', () => {
  const previous = process.env.EXPO_PUBLIC_API_OVERRIDE;
  const address = 'http://192.0.2.10:18080/api/v1';
  process.env.EXPO_PUBLIC_API_OVERRIDE = address;
  try {
    const filename = require.resolve('../apiResolver');
    const compiled = transformSync(readFileSync(filename, 'utf8'), {
      filename,
      babelrc: false,
      configFile: false,
      presets: ['babel-preset-expo'],
      plugins: ['@babel/plugin-transform-modules-commonjs'],
      caller: { name: 'metro', bundler: 'metro', platform: 'android', isDev: true, preserveEnvVars: false },
    });
    const exports: { resolveApiBaseUrl?: () => string } = {};
    runInNewContext(compiled!.code!, {
      module: { exports }, exports, __DEV__: true, process: { env: {} },
      console: { log() {}, warn() {} },
      require(name: string) {
        if (name === 'react-native') return { Platform: { OS: 'android' }, NativeModules: {} };
        if (name === 'expo-device') return { isDevice: true };
        if (name === 'expo-constants') return { __esModule: true, default: { expoConfig: { hostUri: '192.0.2.20:8081' } } };
        return require(name);
      },
    });
    expect(exports.resolveApiBaseUrl!()).toBe(address);
  } finally {
    if (previous === undefined) delete process.env.EXPO_PUBLIC_API_OVERRIDE;
    else process.env.EXPO_PUBLIC_API_OVERRIDE = previous;
  }
});
