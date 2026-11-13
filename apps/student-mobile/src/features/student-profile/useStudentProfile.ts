import { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { profileApi, type StudentProfile } from './profileApi';

export function useStudentProfile(owner: string | undefined) {
  const [result, setResult] = useState<{ owner: string; value?: StudentProfile; failed?: boolean }>();
  const [revision, setRevision] = useState(0);
  const active = useRef<AbortController | null>(null);
  useFocusEffect(useCallback(() => {
    if (!owner) return;
    const request = new AbortController();
    active.current = request;
    setResult(previous => previous?.owner === owner ? { owner, value: previous.value } : { owner });
    void profileApi.get(request.signal).then(value => {
      if (!request.signal.aborted) setResult({ owner, value });
    }).catch(() => {
      if (!request.signal.aborted) setResult(previous => ({
        owner,
        value: previous?.owner === owner ? previous.value : undefined,
        failed: true,
      }));
    });
    return () => {
      request.abort();
      if (active.current === request) active.current = null;
    };
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, revision]));
  const current = result?.owner === owner ? result : undefined;
  return {
    value: current?.value, failed: current?.failed, retry: () => setRevision(n => n + 1),
    accept(value: StudentProfile) {
      if (!owner || !active.current) return;
      active.current.abort();
      setResult({ owner, value });
    },
  };
}
