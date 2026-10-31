import { useCallback, useEffect, useRef, useState } from 'react';
import { quizApi } from './quizApi';

/** Text only. Runs independently of Tutor/review; sequence numbers reject stale responses and edits. */
export function useQuizPreparation(workflowKey: string, problemText: string, confirmed: boolean) {
  const [state, setState] = useState<'IDLE' | 'PREPARING' | 'READY' | 'UNSUPPORTED' | 'FAILED'>('IDLE');
  const [retry, setRetry] = useState(0);
  const revision = useRef(0), requested = useRef(false);
  const retryPreparation = useCallback(() => setRetry(value => value + 1), []);
  useEffect(() => {
    const eligible = confirmed && problemText.trim().length >= 3 && !problemText.includes('[?]');
    if (!eligible && !requested.current) { setState('IDLE'); return; }
    requested.current = true;
    const version = Math.max(Date.now(), revision.current + 1); revision.current = version;
    let current = true;
    let pollTimer: ReturnType<typeof setTimeout> | undefined;
    const poll = async (id: string, remaining: number) => {
      try {
        const response = await quizApi.preparationStatus(id);
        if (!current || revision.current !== version) return;
        if (response.status === 'GENERATING' && remaining > 0) pollTimer = setTimeout(() => { void poll(id, remaining - 1); }, 500);
        else setState(response.status === 'GENERATING' ? 'PREPARING' : response.status === 'INVALIDATED' ? 'IDLE' : response.status);
      } catch { if (current && revision.current === version) setState('FAILED'); }
    };
    setState(eligible ? 'PREPARING' : 'IDLE');
    // Do not abort the edit tombstone: it must reach the server even when the child unmounts.
    void quizApi.prepare(workflowKey, version, eligible ? problemText : '', eligible).then(response => {
      if (current && revision.current === version) {
        if (response.status === 'GENERATING') { setState('PREPARING'); pollTimer = setTimeout(() => { void poll(response.preparationId, 15); }, 300); }
        else setState(response.status === 'INVALIDATED' ? 'IDLE' : response.status);
      }
    }).catch(() => { if (current && revision.current === version) setState('FAILED'); });
    return () => { current = false; clearTimeout(pollTimer); };
  }, [workflowKey, problemText, confirmed, retry]);
  return { state, retry: retryPreparation };
}
