import React, { createContext, useCallback, useEffect, useState, useContext } from 'react';
import { AppState } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { createNarrationCache, type NarrationCache } from './narrationCache';
import { prepareLessonMedia, type NarrationSource } from './narrationApi';
import { readNarrationVoice, subscribeNarrationVoice, type NarrationVoice } from './narrationVoices';

export const NarrationCacheContext = createContext<NarrationCache | null>(null);

export function NarrationPreparation({ children }: { children: React.ReactNode }) {
  const [cache] = useState(createNarrationCache);
  useEffect(() => () => cache.clear(), [cache]);
  return <NarrationCacheContext.Provider value={cache}>{children}</NarrationCacheContext.Provider>;
}

/** Prepare only issued text while the pupil reads. No playback or future answers. */
export function useNarrationPreparation(source: NarrationSource | null, paragraphs: string[]) {
  const cache = useContext(NarrationCacheContext);
  const sessionId = source?.sessionId, revision = source?.revision, text = JSON.stringify(paragraphs);
  useFocusEffect(useCallback(() => {
    if (!cache || !sessionId || revision === undefined || !JSON.parse(text).some((part: string) => part.trim())) return;
    let active = true, generation = 0;
    let foreground = AppState.currentState !== 'background' && AppState.currentState !== 'inactive';
    let chosen: NarrationVoice | undefined;
    const leases = new Set<ReturnType<NarrationCache['acquire']>>();
    const controls = new Set<AbortController>();
    const stop = () => { ++generation; leases.forEach(lease => lease.release()); leases.clear(); controls.forEach(control => control.abort()); controls.clear(); };
    const begin = async () => {
      stop(); const id = generation;
      const selected = chosen || await readNarrationVoice();
      if (!active || generation !== id) return;
      const control = new AbortController();
      controls.add(control);
      // Only session identity and preference are sent: private future scripts stay on the server.
      void prepareLessonMedia({ sessionId, revision }, selected, control.signal).catch(() => {});
      // The server already warms both voices. Do not start a competing public
      // job for the unselected voice while it is preparing the next lesson step.
      const lease = cache.acquire({ sessionId, revision }, JSON.parse(text), selected, true);
      leases.add(lease);
      try { await lease.promise; }
      catch { /* Speculative failure never blocks reading or poisons a retry. */ }
    };
    if (foreground) void begin();
    const listener = AppState.addEventListener('change', state => {
      foreground = state === 'active';
      if (foreground) void begin(); else stop();
    });
    const unsubscribe = subscribeNarrationVoice(voice => {
      chosen = voice;
      if (foreground) void begin();
    });
    return () => { active = false; stop(); listener.remove(); unsubscribe(); };
  }, [cache, sessionId, revision, text]));
}
