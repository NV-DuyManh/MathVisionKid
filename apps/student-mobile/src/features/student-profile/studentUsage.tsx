import { useContext, useEffect } from 'react';
import { AppState, Platform } from 'react-native';
import { AuthContext } from '../../context/AuthContext';
import apiClient from '../../services/api/apiClient';
import { tokenStorage } from '../../services/auth/tokenStorage';

const HEARTBEAT_MS = 10_000;

export type StudentUsageWeek = { today: string; totalMillis: number; days: { date: string; elapsedMillis: number }[] };

export async function readStudentUsageWeek(signal: AbortSignal) {
  return (await apiClient.get<StudentUsageWeek>('/student/app-usage/week', { signal })).data;
}

function connectionId() {
  return globalThis.crypto?.randomUUID?.() ?? 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, character => {
    const random = Math.floor(Math.random() * 16);
    return (character === 'x' ? random : (random & 3) | 8).toString(16);
  });
}

export function StudentUsageTracker() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  const eligible = auth?.isAuthenticated === true && auth.user?.role === 'STUDENT' && auth.user?.active === true && !!owner;

  useEffect(() => {
    if (!eligible) return;
    let mounted = true;
    let running: string | undefined;
    let interval: ReturnType<typeof setInterval> | undefined;
    let requests: Promise<unknown> = Promise.resolve();
    const session = tokenStorage.getSessionId();
    const send = (id: string, active: boolean) => {
      requests = requests.catch(() => {}).then(async () => {
        if (active && (!mounted || id !== running)) return;
        const identity = await session;
        if (identity === null || identity !== await tokenStorage.getSessionId()) return;
        const options = { timeout: 4_000, _identity: identity };
        await apiClient.post('/student/app-usage/heartbeat', { connectionId: id, active }, options);
      }).catch(() => { /* A lost heartbeat expires server-side. */ });
    };
    const start = () => {
      if (!mounted || running) return;
      const id = connectionId();
      running = id;
      send(id, true);
      interval = setInterval(() => send(id, true), HEARTBEAT_MS);
    };
    const stop = () => {
      clearInterval(interval);
      if (!running) return;
      const id = running;
      running = undefined;
      send(id, false);
    };

    if (Platform.OS === 'web') {
      const updateVisibility = () => { if (document.visibilityState === 'visible') start(); else stop(); };
      updateVisibility();
      document.addEventListener('visibilitychange', updateVisibility);
      window.addEventListener('pagehide', stop);
      window.addEventListener('pageshow', updateVisibility);
      return () => {
        mounted = false;
        document.removeEventListener('visibilitychange', updateVisibility);
        window.removeEventListener('pagehide', stop);
        window.removeEventListener('pageshow', updateVisibility);
        stop();
      };
    }

    if (AppState.currentState !== 'inactive' && AppState.currentState !== 'background') start();
    const change = AppState.addEventListener('change', state => { if (state === 'active') start(); else stop(); });
    return () => { mounted = false; change.remove(); stop(); };
  }, [eligible, owner]);

  return null;
}
