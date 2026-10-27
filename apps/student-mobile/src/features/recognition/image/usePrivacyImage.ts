import { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { inspectReadableImage, logStageDiagnostic, ReadableImage } from './imagePipeline';

type Status = 'loading' | 'ready' | 'error';
type Request = { id: string; active: boolean; status: Status; stop: () => void };
type Snapshot = { requestId: string; status: Status; size: ReadableImage | null };

/** One attempt per focus/retry. Native start events are observational, never resets. */
export function usePrivacyImage(uri: string) {
  const sequence = useRef(0);
  const current = useRef<Request | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [snapshot, setSnapshot] = useState<Snapshot>({ requestId: '', status: 'loading', size: null });
  useFocusEffect(useCallback(() => {
    const request: Request = { id: `${++sequence.current}:${attempt}`, active: true, status: 'loading', stop: () => {} };
    current.current = request;
    setSnapshot({ requestId: request.id, status: 'loading', size: null });
    const fail = () => {
      if (!request.active || current.current !== request || request.status !== 'loading') return;
      request.status = 'error';
      request.stop();
      logStageDiagnostic('PRIVACY_LOAD_ERROR', { uri, extra: `attempt=${request.id} verification-or-load-timeout` });
      setSnapshot(previous => ({ ...previous, status: 'error' }));
    };
    // A deadline only exposes an error. It never supplies loading success.
    const timer = setTimeout(fail, 15000);
    request.stop = () => clearTimeout(timer);
    void inspectReadableImage(uri).then(size => {
      if (!request.active || current.current !== request || request.status !== 'loading') return;
      setSnapshot({ requestId: request.id, status: 'loading', size });
    }, fail);
    return () => { request.active = false; request.stop(); };
  }, [uri, attempt]));

  const requestId = snapshot.requestId;
  const isAttemptActive = useCallback(() => {
    const request = current.current;
    return !!request && request.active && request.id === requestId;
  }, [requestId]);
  const onLoadStart = useCallback(() => {
    if (isAttemptActive()) logStageDiagnostic('PRIVACY_LOAD_START', { uri, extra: `attempt=${requestId} status=${current.current!.status}` });
    // Cached iOS responses and layout updates can emit start after success.
  }, [isAttemptActive, requestId, uri]);
  const onLoad = useCallback(() => {
    const request = current.current;
    if (!isAttemptActive() || request!.status !== 'loading' || !snapshot.size) return;
    request!.status = 'ready'; request!.stop();
    logStageDiagnostic('PRIVACY_LOAD_SUCCESS', { ...snapshot.size, extra: `attempt=${requestId}` });
    setSnapshot(previous => ({ ...previous, status: 'ready' }));
  }, [isAttemptActive, requestId, snapshot.size]);
  const onError = useCallback(() => {
    const request = current.current;
    if (!isAttemptActive() || request!.status === 'error') return;
    request!.status = 'error'; request!.stop();
    logStageDiagnostic('PRIVACY_LOAD_ERROR', { uri, extra: `attempt=${requestId} native-error` });
    setSnapshot(previous => ({ ...previous, status: 'error' }));
  }, [isAttemptActive, requestId, uri]);
  const retry = useCallback(() => setAttempt(value => value + 1), []);
  const isCurrent = useCallback(() => isAttemptActive() && current.current!.status === 'ready', [isAttemptActive]);
  return {
    imageKey: requestId, sourceSize: snapshot.size,
    imageLoaded: snapshot.status === 'ready', imageLoadError: snapshot.status === 'error',
    isCurrent, onLoadStart, onLoad, onError, retry,
  };
}
