/** Bound disk-cache I/O: Metro otherwise opens large cache graphs concurrently,
 * which can exceed Windows file-handle limits (EMFILE). Errors still propagate. */
function boundedCacheStore(store, concurrency = 32) {
  if (!Number.isInteger(concurrency) || concurrency < 1) throw new RangeError('Invalid cache concurrency');
  const pending = [];
  let head = 0;
  let active = 0;
  function drain() {
    while (active < concurrency && head < pending.length) {
      const { operation, resolve, reject } = pending[head];
      pending[head++] = undefined;
      active++;
      Promise.resolve().then(operation).then(resolve, reject).finally(() => { active--; drain(); });
    }
    if (head === pending.length) { pending.length = 0; head = 0; }
    else if (head >= 1024 && head * 2 >= pending.length) { pending.splice(0, head); head = 0; }
  }
  function run(operation) {
    return new Promise((resolve, reject) => { pending.push({ operation, resolve, reject }); drain(); });
  }
  return {
    name: 'MathVisionKid bounded disk cache',
    get: key => run(() => store.get(key)),
    set: (key, value) => run(() => store.set(key, value)),
    // Metro invokes clear at startup, before it queues transform-cache requests.
    clear: () => store.clear(),
  };
}
module.exports = { boundedCacheStore };
