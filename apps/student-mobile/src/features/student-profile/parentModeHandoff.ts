import type { ParentSettings } from './parentControlApi';

const HANDOFF_TTL_MS = 15_000;
const pendingSettings = new Map<string, { settings: ParentSettings; expiresAt: number }>();
const activeSessions = new Map<string, ParentSettings>();

export function storeParentModeHandoff(owner: string, settings: ParentSettings) {
  pendingSettings.clear();
  activeSessions.clear();
  pendingSettings.set(owner, { settings, expiresAt: Date.now() + HANDOFF_TTL_MS });
  activeSessions.set(owner, settings);
}

export function consumeParentModeHandoff(owner: string) {
  const handoff = pendingSettings.get(owner);
  pendingSettings.clear();
  return handoff && handoff.expiresAt > Date.now() ? handoff.settings : undefined;
}

export function readParentModeSession(owner: string) {
  return activeSessions.get(owner);
}

export function updateParentModeSession(owner: string, settings: ParentSettings) {
  if (activeSessions.has(owner)) {
    activeSessions.set(owner, settings);
  }
}

export function clearParentModeSession() {
  pendingSettings.clear();
  activeSessions.clear();
}
