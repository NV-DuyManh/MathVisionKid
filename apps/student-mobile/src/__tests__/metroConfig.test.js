const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const expoRoot = path.dirname(require.resolve('expo/package.json'));
const expoCliRoot = path.dirname(require.resolve('@expo/cli/package.json', { paths: [expoRoot] }));
const { composeMetroIgnorePatterns } = require(path.join(expoCliRoot, 'build/src/utils/composeMetroIgnorePatterns.js'));

const source = fs.readFileSync(path.resolve(__dirname, '../../metro.config.js'), 'utf8');

function loadConfig(root, paths, defaultBlockList) {
  const config = { resolver: { blockList: defaultBlockList } };
  const cache = { boundedCacheStore: jest.fn((store, concurrency) => ({ store, concurrency })) };
  const context = {
    __dirname: paths.join(root, 'apps', 'student-mobile'),
    module: { exports: {} },
    process: { platform: paths === path.win32 ? 'win32' : 'linux' },
    require: name => ({
      'expo/metro-config': { getDefaultConfig: () => config },
      path: paths,
      os: { tmpdir: () => paths === path.win32 ? 'C:\\Temp' : '/tmp' },
      fs: { mkdirSync: jest.fn() },
      './metroCache.cjs': cache,
    })[name],
  };
  vm.runInNewContext(source, context, { filename: 'metro.config.js' });
  return { config: context.module.exports, cache };
}

describe.each([
  ['Windows', 'E:\\MathVisionKid [work]+', path.win32],
  ['Linux', '/workspace/MathVisionKid [work]+', path.posix],
])('%s root-anchored Metro exclusions', (_platform, root, paths) => {
  const blocked = (config, file) => config.resolver.blockList.some(pattern => pattern.test(file));

  it('excludes generated/service roots with either separator and exact directory boundaries', () => {
    const { config } = loadConfig(root, paths);
    for (const folder of ['report', 'reports', 'runtime', 'ai', 'ai-training', 'backend', 'output', 'scratch',
      'xyz', 'datasets', 'models', '.git', '.venv', '.local-artifacts', 'demoUI', 'infra/local-runtime']) {
      const file = paths.join(root, ...folder.split('/'), 'generated', 'large-file.bin');
      expect(blocked(config, file)).toBe(true);
      expect(blocked(config, file.replace(/\\/g, '/'))).toBe(true);
      expect(blocked(config, file.replace(/\//g, '\\'))).toBe(true);
      expect(blocked(config, paths.join(root, ...folder.split('/')))).toBe(true);
    }
    expect(blocked(config, paths.join(root, 'reporting', 'index.ts'))).toBe(false);
    expect(blocked(config, paths.join(root, 'models-shared', 'index.ts'))).toBe(false);
  });

  it('preserves Student source, assets, shared packages, vendor and hoisted dependencies', () => {
    const { config } = loadConfig(root, paths);
    for (const relative of ['apps/student-mobile/src/app/index.tsx', 'apps/student-mobile/assets/models/figure.png',
      'apps/student-mobile/node_modules/report/index.js', 'packages/report/src/index.ts',
      'vendor/report/index.js', 'node_modules/report/index.js', 'node_modules/ai/index.js',
      'node_modules/dependency/infra/local-runtime/index.js', 'contracts/tutor.json']) {
      expect(blocked(config, paths.join(root, ...relative.split('/')))).toBe(false);
    }
    expect(blocked(config, paths.join(paths.dirname(root), 'another-project', 'report', 'index.ts'))).toBe(false);
    expect(blocked(config, paths.join(`${root}-other`, 'report', 'index.ts'))).toBe(false);
    expect(config.watchFolders).toEqual([root]);
    expect(config.resolver.nodeModulesPaths).toEqual([
      paths.join(root, 'apps', 'student-mobile', 'node_modules'), paths.join(root, 'node_modules'),
    ]);
  });

  it('composes with Expo SDK 58 built-in ignore patterns using its installed composer', () => {
    const expoDefaults = /([.]expo\\types|[.]expo\\web\\cache|\\__tests__\\.*)$/;
    const { config } = loadConfig(root, paths, [expoDefaults]);
    expect(config.resolver.blockList.every(pattern => pattern.flags === expoDefaults.flags)).toBe(true);
    const combined = composeMetroIgnorePatterns(config.resolver.blockList);
    expect(combined.test(paths.join(root, 'report', 'generated.bin'))).toBe(true);
    expect(combined.test(paths.join(root, 'apps', 'student-mobile', 'src', 'index.tsx'))).toBe(false);
    expect(combined.test(paths.join(root, 'node_modules', 'report', 'index.js'))).toBe(false);
  });

  it.each(['array', 'single', 'missing'])('preserves %s default blocklist and the bounded cache guard', format => {
    const defaultPattern = /default-exclusion/;
    const { config, cache } = loadConfig(root, paths,
      format === 'array' ? [defaultPattern] : format === 'single' ? defaultPattern : undefined);
    expect(config.resolver.blockList).toHaveLength(format === 'missing' ? 1 : 2);
    if (format !== 'missing') expect(config.resolver.blockList[0]).toBe(defaultPattern);
    class FileStore { constructor(options) { this.options = options; } }
    const stores = config.cacheStores({ FileStore });
    expect(cache.boundedCacheStore).toHaveBeenCalledWith(expect.any(FileStore), 32);
    expect(stores).toHaveLength(1);
    expect(blocked(config, stores[0].store.options.root)).toBe(false);
  });
});
