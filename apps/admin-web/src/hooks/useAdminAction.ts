import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
export function useAdminAction() {
  const queryClient = useQueryClient();
  const alive = useRef(true);
  const lock = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [notice, setNotice] = useState('');
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  async function run<T>(action: () => Promise<T>, success?: (data: T) => void) {
    if (lock.current) return;
    lock.current = true;
    setPending(true); setError(null); setNotice('');
    try {
      const data = await action();
      if (!alive.current) return;
      await queryClient.invalidateQueries({ predicate: query => String(query.queryKey[0]).startsWith('admin-') });
      if (alive.current) { success?.(data); setNotice('Đã lưu thay đổi thành công.'); }
    } catch (cause) { if (alive.current) {
      const e = cause as { response?: { status?: number }; code?: string };
      setError({ response: e?.response ? { status: e.response.status } : undefined, code: e?.code });
    } }
    finally { lock.current = false; if (alive.current) setPending(false); }
  }
  return { pending, error, notice, run, clear: () => { setError(null); setNotice(''); } };
}
