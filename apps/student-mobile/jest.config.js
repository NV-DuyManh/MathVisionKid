const path = require('node:path');
const expoPreset = require('jest-expo/jest-preset');
const [babelTransform, babelOptions] = expoPreset.transform['\\.[jt]sx?$'];

module.exports = {
  preset: 'jest-expo',
  // Tests change public configuration between cases instead of bundling one value.
  transform: {
    '\\.[jt]sx?$': [babelTransform, { ...babelOptions, caller: { ...babelOptions.caller, preserveEnvVars: true } }],
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: require('jest-expo/jest-preset').transformIgnorePatterns.map(pattern => pattern.replace('(?!(.pnpm|', '(?!(.pnpm|@mathvisionkid/training-games|')),
  // Jest 30 also discovers .mjs; these existing files use Node's test runner.
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
  moduleNameMapper: {
    // Use Expo's own core dependency even when npm keeps it nested under Expo.
    '^expo-modules-core$': require.resolve('expo-modules-core', {
      paths: [path.dirname(require.resolve('expo/package.json'))],
    }),
  },
};
