// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    settings: {
      'import/resolver': {
        typescript: { project: __dirname + '/tsconfig.json' },
      },
    },
  },
  {
    ignores: ["**/dist/**", "**/build/**", "**/generated/**", "**/coverage/**", "**/.expo/**", "node_modules/**", "**/.venv/**", "**/scratch/**", "**/scripts/**", "**/.agents/**", "**/__tests__/**"],
  }
]);
