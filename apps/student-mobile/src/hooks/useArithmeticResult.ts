import { useEffect, useState } from 'react';
import { getSubmissionService } from '../services/api/SubmissionServiceFactory';
import { SubmissionResult } from '../types';
import { parseSubmissionResult } from '../utils/resultRouting';

/** Reload by stable submission identity, including direct links and reopened result screens. */
export function useArithmeticResult(data?: string, submissionId?: string) {
  const initial = parseSubmissionResult(data);
  const id = submissionId || initial?.id;
  const [loaded, setLoaded] = useState<{ id?: string; result: SubmissionResult | null; loading: boolean }>(() => ({ id, result: null, loading: Boolean(id) }));
  // Reset on every identity change, including returning to a previous pending request.
  if (loaded.id !== id) setLoaded({ id, result: null, loading: Boolean(id) });
  useEffect(() => {
    const controller = new AbortController();
    if (id) {
      getSubmissionService().getSubmission(id, undefined, controller.signal)
        .then(current => { if (!controller.signal.aborted) setLoaded({ id, result: current, loading: false }); })
        .catch(() => { if (!controller.signal.aborted) setLoaded({ id, result: null, loading: false }); });
    }
    return () => controller.abort();
  }, [id]);
  return { result: loaded.id === id ? loaded.result : null, loading: loaded.id === id ? loaded.loading : Boolean(id) };
}
