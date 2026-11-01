type SessionFailure = 'expired' | 'forbidden';
const listeners = new Set<(reason: SessionFailure) => void>();
export const sessionEvents = {
  subscribe(listener: (reason: SessionFailure) => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
  expired(reason: SessionFailure = 'expired') { listeners.forEach(listener => listener(reason)); },
};
