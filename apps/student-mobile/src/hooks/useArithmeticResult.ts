import { useEffect, useState } from 'react';
import { getSubmissionService } from '../services/api/SubmissionServiceFactory';
import { SubmissionResult } from '../types';
import { parseSubmissionResult } from '../utils/resultRouting';

/** Reload by stable submission identity, including direct links and reopened result screens. */
export function useArithmeticResult(data?: string, submissionId?: string) {
  const initial = parseSubmissionResult(data);
  const id = submissionId || initial?.id;
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [loading, setLoading] = useState(Boolean(id));
  useEffect(() => {
    const controller = new AbortController();
    setResult(null);
    setLoading(Boolean(id));
    if (id) {
      getSubmissionService().getSubmission(id, undefined, controller.signal)
        .then(current => { if (!controller.signal.aborted) setResult(current); })
        .catch(() => { /* Keep missing results ungraded; the screen offers a safe way back. */ })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }
    return () => controller.abort();
  }, [id]);
  return { result, loading };
}
