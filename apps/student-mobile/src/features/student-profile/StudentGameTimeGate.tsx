import { useContext, useEffect, useState, type PropsWithChildren } from 'react';
import { ActivityIndicator, AppState, Platform, View } from 'react-native';
import apiClient from '../../services/api/apiClient';
import { tokenStorage } from '../../services/auth/tokenStorage';
import { createUsageConnectionId } from './studentUsage';
import { StudentPauseScreen } from './StudentPauseScreen';
import { StudentGameAccess, VerifyStudentGameAccess } from './StudentDailyLimit';

const RENEW_MS = 4_000;
type GameLease = { leaseMillis: number; remainingMillis: number | null; gameLimitReached: boolean };
type Playback = 'checking' | 'ready' | 'connection' | 'game-limit';

type GateProps = PropsWithChildren<{ onLeave: () => void }>;

export function StudentGameTimeGate({ children, onLeave }: GateProps) {
  const mayPlay = useContext(StudentGameAccess);
  const verify = useContext(VerifyStudentGameAccess);
  const [checking, setChecking] = useState(false);
  const [retryFailed, setRetryFailed] = useState(false);
  if (mayPlay) return <PlaybackLease onLeave={onLeave}>{children}</PlaybackLease>;
  return <StudentPauseScreen reason="connection" checking={checking} retryFailed={retryFailed} onLeave={onLeave}
    onContinue={() => {
      setChecking(true);
      void verify().then(result => setRetryFailed(!result), () => setRetryFailed(true)).finally(() => setChecking(false));
    }} />;
}

function PlaybackLease({ children, onLeave }: GateProps) {
  const [state, setState] = useState<Playback>('checking');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let mounted = true;
    let activeId: string | undefined;
    let renewal: ReturnType<typeof setInterval> | undefined;
    let expiration: ReturnType<typeof setTimeout> | undefined;
    let pending: Promise<void> | undefined;
    let validUntil = 0;
    const session = tokenStorage.getSessionId();
    const visible = () => Platform.OS === 'web'
      ? document.visibilityState === 'visible' && navigator.onLine
      : AppState.currentState === 'active' || AppState.currentState == null;

    async function heartbeat(id: string, active: boolean) {
      const identity = await session;
      if (!identity || identity !== await tokenStorage.getSessionId()) throw new Error('Phiên đăng nhập đã thay đổi.');
      if (active && (!mounted || id !== activeId)) return undefined;
      const options = { timeout: 3_500, _identity: identity };
      return (await apiClient.post<GameLease>('/student/app-usage/game-heartbeat', { connectionId: id, active }, options)).data;
    }

    function stop() {
      clearInterval(renewal);
      clearTimeout(expiration);
      validUntil = 0;
      const id = activeId;
      activeId = undefined;
      if (id) void Promise.resolve(pending).then(() => heartbeat(id, false)).catch(() => {});
    }

    function renew() {
      const id = activeId;
      if (!id || pending) return;
      const requestedAt = performance.now();
      pending = heartbeat(id, true).then(result => {
        if (!mounted || id !== activeId || !visible()) return;
        clearTimeout(expiration);
        const lease = result?.leaseMillis;
        if (result?.gameLimitReached) {
          stop();
          setState('game-limit');
          return;
        }
        if (typeof lease !== 'number' || !Number.isFinite(lease) || requestedAt + lease <= performance.now()) {
          stop();
          setState('connection');
          return;
        }
        const cutoff = requestedAt + lease;
        validUntil = cutoff;
        expiration = setTimeout(() => {
          // A throttled or disconnected client cannot extend a server lease.
          stop();
          setState(result?.remainingMillis === lease ? 'game-limit' : 'connection');
        }, Math.max(0, cutoff - performance.now()));
        setState('ready');
      }).catch((error: unknown) => {
        if (!mounted || id !== activeId) return;
        const status = (error as { response?: { status?: number } } | null)?.response?.status;
        // Retry temporary failures within the existing server grant. Never
        // extend its deadline or ignore an explicit rejection.
        if (typeof status === 'number' && status >= 500 && performance.now() < validUntil) return;
        stop();
        setState('connection');
      }).finally(() => {
        pending = undefined;
        if (mounted && activeId && activeId !== id) renew();
      });
    }

    function syncVisibility() {
      if (!visible()) {
        stop();
        setState('connection');
      } else if (!activeId) {
        setState('checking');
        activeId = createUsageConnectionId();
        renew();
        renewal = setInterval(renew, RENEW_MS);
      }
    }

    function onPageHide() {
      stop();
      setState('connection');
    }

    syncVisibility();
    if (Platform.OS === 'web') {
      document.addEventListener('visibilitychange', syncVisibility);
      window.addEventListener('online', syncVisibility);
      window.addEventListener('offline', syncVisibility);
      window.addEventListener('pageshow', syncVisibility);
      window.addEventListener('pagehide', onPageHide);
    }
    const app = Platform.OS !== 'web' ? AppState.addEventListener('change', syncVisibility) : undefined;
    return () => {
      mounted = false;
      stop();
      app?.remove();
      if (Platform.OS === 'web') {
        document.removeEventListener('visibilitychange', syncVisibility);
        window.removeEventListener('online', syncVisibility);
        window.removeEventListener('offline', syncVisibility);
        window.removeEventListener('pageshow', syncVisibility);
        window.removeEventListener('pagehide', onPageHide);
      }
    };
  }, [attempt]);

  if (state === 'ready') return children;
  if (state === 'checking') return <View style={{ flex: 1, justifyContent: 'center' }}>
    <ActivityIndicator accessibilityLabel="Đang kiểm tra thời gian chơi" />
  </View>;
  return <StudentPauseScreen reason={state === 'game-limit' ? state : 'connection'} onLeave={onLeave}
    onContinue={() => { setState('checking'); setAttempt(value => value + 1); }} />;
}
