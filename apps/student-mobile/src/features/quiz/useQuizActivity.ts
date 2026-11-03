import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Quiz, quizApi } from './quizApi';

/** Server leases bound lost connections; leaving the screen pauses immediately. */
export function useQuizActivity(quiz: Quiz | null) {
  const [elapsed, setElapsed] = useState(quiz?.elapsedMillis || 0);
  const [previousQuiz, setPreviousQuiz] = useState(quiz);
  // Reset before committing a changed question; do not render the previous quiz's timer first.
  if (previousQuiz !== quiz) {
    setPreviousQuiz(quiz);
    setElapsed(quiz?.elapsedMillis || 0);
  }
  const baseline = useRef({ elapsed: 0, received: 0, running: false });
  useEffect(() => {
    baseline.current = { elapsed: quiz?.elapsedMillis || 0, received: performance.now(), running: baseline.current.running && quiz?.status === 'IN_PROGRESS' };
  }, [quiz]);
  const id = quiz?.quizId, run = quiz?.startedAt, status = quiz?.status;
  useFocusEffect(useCallback(() => {
    if (!id || !run || status !== 'IN_PROGRESS') return;
    let mounted = true, foreground = false, request: AbortController | null = null, generation = 0;
    const current = () => baseline.current.elapsed + (baseline.current.running ? Math.min(12000, Math.max(0, performance.now() - baseline.current.received)) : 0);
    const heartbeat = () => {
      if (!foreground || request) return;
      const abort = new AbortController(), version = generation; request = abort;
      void quizApi.activity(id, run, true, abort.signal).then(next => {
        if (!mounted || !foreground || version !== generation || next.startedAt !== run || next.status !== 'IN_PROGRESS') return;
        baseline.current = { elapsed: next.elapsedMillis, received: performance.now(), running: next.timerRunning === true };
        setElapsed(next.elapsedMillis);
      }).catch(() => { /* Keep the last confirmed duration; never grow beyond a lease. */ })
        .finally(() => { if (request === abort) request = null; });
    };
    const pause = () => {
      foreground = false; ++generation;
      const duration = current(); baseline.current = { elapsed: duration, received: performance.now(), running: false };
      if (mounted) setElapsed(duration);
      request?.abort(); request = null;
      void quizApi.activity(id, run, false).catch(() => {});
    };
    const change = (state: string) => {
      if (state === 'active' && !foreground) { foreground = true; heartbeat(); }
      else if (state !== 'active' && foreground) pause();
    };
    const initial = AppState.currentState;
    change(initial === 'background' || initial === 'inactive' ? initial : 'active');
    const listener = AppState.addEventListener('change', change);
    const heartbeatTimer = setInterval(heartbeat, 4000);
    const clock = setInterval(() => { if (foreground) setElapsed(current()); }, 1000);
    return () => { mounted = false; clearInterval(clock); clearInterval(heartbeatTimer); listener.remove(); pause(); };
  }, [id, run, status]));
  return elapsed;
}
