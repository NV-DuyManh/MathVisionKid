const { boundedCacheStore } = require('../../metroCache.cjs');

test('cache reads and writes share a bounded I/O budget without losing values', async () => {
  let active = 0, peak = 0;
  const rows = new Map();
  const operation = async fn => { active++; peak = Math.max(peak, active); await new Promise(resolve => setTimeout(resolve, 1)); try { return fn(); } finally { active--; } };
  const store = boundedCacheStore({ get: key => operation(() => rows.get(key) ?? null), set: (key, value) => operation(() => rows.set(key, value)), clear: () => rows.clear() }, 4);
  await Promise.all(Array.from({ length: 60 }, (_, i) => store.set(i, `value-${i}`)));
  const values = await Promise.all(Array.from({ length: 60 }, (_, i) => store.get(i)));
  expect(peak).toBe(4); expect(active).toBe(0);
  expect(values).toEqual(Array.from({ length: 60 }, (_, i) => `value-${i}`));
  store.clear(); expect(await store.get(0)).toBeNull();
});

test('a cache error reaches the caller and releases its slot for the next operation', async () => {
  const failure = new Error('disk unavailable');
  const store = boundedCacheStore({ get: key => { if (key === 'bad') throw failure; return 'ok'; }, set: () => {}, clear: () => {} }, 1);
  const bad = store.get('bad'), good = store.get('next');
  await expect(bad).rejects.toBe(failure); await expect(good).resolves.toBe('ok');
});

test('invalid limits fail immediately instead of silently blocking Metro forever', () => {
  expect(() => boundedCacheStore({}, 0)).toThrow(RangeError);
});
