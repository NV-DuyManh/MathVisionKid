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

// 1. Watch all files within the monorepo
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

module.exports = config;
