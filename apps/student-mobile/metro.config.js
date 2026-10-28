// Learn more: https://docs.expo.dev/guides/monorepos/
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const os = require('os');
const fs = require('fs');
const { boundedCacheStore } = require('./metroCache.cjs');

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);
const cacheRoot = path.join(os.tmpdir(), 'mathvisionkid-student-mobile-metro-sdk58');
config.cacheStores = ({ FileStore }) => [boundedCacheStore(new FileStore({ root: path.join(cacheRoot, 'transforms') }), 32)];
config.fileMapCacheDirectory = path.join(cacheRoot, 'file-map');
fs.mkdirSync(config.fileMapCacheDirectory, { recursive: true });

// Shared packages and hoisted dependencies still live outside the app directory.
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

// Keep generated data, models and local services out of Metro's file map.
// Anchor at this repository so packages/assets with the same names remain valid.
const defaultBlockList = config.resolver.blockList;
const separator = '[/\\\\]';
const escapeRegex = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const rootPattern = monorepoRoot.split(/[/\\]/).map(escapeRegex).join(separator);
const excludedFolders = ['report', 'reports', 'runtime', 'ai', 'ai-training', 'backend', 'output', 'scratch',
  'xyz', 'datasets', 'models', '.git', '.venv', 'infra/local-runtime'];
const excludedPattern = excludedFolders.map(folder => folder.split('/').map(escapeRegex).join(separator)).join('|');
config.resolver.blockList = [
  ...(Array.isArray(defaultBlockList) ? defaultBlockList : defaultBlockList ? [defaultBlockList] : []),
  new RegExp(`^${rootPattern}${separator}(?:${excludedPattern})(?:${separator}|$)`),
];

module.exports = config;
