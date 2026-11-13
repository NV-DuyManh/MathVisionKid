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
    setResult({ owner });
    void profileApi.get(request.signal).then(value => {
      if (!request.signal.aborted) setResult({ owner, value });
    }).catch(() => {
      if (!request.signal.aborted) setResult({ owner, failed: true });
    });
    return () => request.abort();
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, revision]));
  const current = result?.owner === owner ? result : undefined;
  return {
    value: current?.value, failed: current?.failed, retry: () => setRevision(n => n + 1),
    accept(value: StudentProfile) {
      if (owner && active.current && !active.current.signal.aborted) setResult({ owner, value });
    },
  };
}
