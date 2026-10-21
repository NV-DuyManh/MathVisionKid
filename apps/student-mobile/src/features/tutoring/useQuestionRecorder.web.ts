import { useMemo, useRef, useState } from 'react';

/** Explicitly release browser tracks, including a permission request resolved after dismissal. */
export function useQuestionRecorder() {
  const [durationMillis, setDurationMillis] = useState(0);
  const stream = useRef<MediaStream | null>(null), media = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]), generation = useRef(0), callback = useRef<(() => void) | null>(null);
  const tick = useRef<ReturnType<typeof setInterval> | null>(null), limit = useRef<ReturnType<typeof setTimeout> | null>(null);
  const done = useRef<Promise<string | null> | null>(null), url = useRef<string | null>(null);
  const recorder = useMemo(() => {
    const clear = () => { if (tick.current) clearInterval(tick.current); if (limit.current) clearTimeout(limit.current); tick.current = null; limit.current = null; };
    const release = () => { stream.current?.getTracks().forEach(track => track.stop()); stream.current = null; };
    return {
      async prepare() {
        const id = ++generation.current;
        if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('Microphone unavailable');
        const acquired = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (id !== generation.current) { acquired.getTracks().forEach(track => track.stop()); throw new Error('Recording canceled'); }
        stream.current = acquired;
        const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'].find(type => MediaRecorder.isTypeSupported(type));
        if (!mimeType) { release(); throw new Error('Recording unsupported'); }
        media.current = new MediaRecorder(acquired, { mimeType, audioBitsPerSecond: 64000 });
        chunks.current = []; url.current = null; setDurationMillis(0);
      },
      start(onFinish: () => void) {
        const current = media.current; if (!current) throw new Error('Recording not ready');
        const id = generation.current;
        callback.current = onFinish;
        done.current = new Promise(resolve => {
          current.ondataavailable = event => { if (event.data.size) chunks.current.push(event.data); };
          current.onstop = () => {
            clear(); release();
            if (id === generation.current) url.current = URL.createObjectURL(new Blob(chunks.current, { type: current.mimeType }));
            chunks.current = []; resolve(id === generation.current ? url.current : null);
            callback.current?.();
          };
          current.onerror = () => { clear(); release(); resolve(null); callback.current?.(); };
        });
        current.start(); const started = Date.now();
        tick.current = setInterval(() => setDurationMillis(Math.min(30000, Date.now() - started)), 250);
        limit.current = setTimeout(() => { if (current.state !== 'inactive') current.stop(); }, 30000);
      },
      async stop(): Promise<string | null> {
        // Invalidate a pending permission/prepare even when no recorder exists.
        const recording = media.current;
        callback.current = null; clear();
        if (recording && recording.state !== 'inactive') {
          recording.stop(); const result = await done.current; media.current = null; return result;
        }
        release(); generation.current++; media.current = null;
        return url.current;
      },
    };
  }, []);
  return { recorder, durationMillis };
}
