import React, { createContext, useCallback, useEffect, useMemo, useContext } from 'react';
import { AppState } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { createNarrationCache, type NarrationCache } from './narrationCache';
import { prepareLessonMedia, type NarrationSource, type downloadNarration } from './narrationApi';
import { NARRATION_VOICES, readNarrationVoice, subscribeNarrationVoice, isNarrationVoice, type NarrationChoice, type NarrationVoice } from './narrationVoices';
import { createPlaybackBookmarks } from './playbackBookmarks';

export const NarrationCacheContext = createContext<NarrationCache | null>(null);
export const PlaybackBookmarksContext = createContext<ReturnType<typeof createPlaybackBookmarks> | null>(null);

export function NarrationPreparation({ children, owner, download }: { children: React.ReactNode; owner?: string; download?: typeof downloadNarration }) {
  // Quiz keeps the same cache/player lifecycle, with its own authorized endpoint.
  const cache = useMemo(() => createNarrationCache(download ? { download, prioritize: null } : undefined), [download, owner]);
  const bookmarks = useMemo(() => createPlaybackBookmarks(owner), [owner]);
  useEffect(() => () => cache.clear(), [cache]);
  useEffect(()=>{
    const flush=()=>{void bookmarks.flush();};
    if(typeof window!=='undefined'&&window.addEventListener)window.addEventListener('pagehide',flush);
    return()=>{if(typeof window!=='undefined'&&window.removeEventListener)window.removeEventListener('pagehide',flush);flush();};
  },[bookmarks]);
  return <NarrationCacheContext.Provider value={cache}><PlaybackBookmarksContext.Provider value={bookmarks}>{children}</PlaybackBookmarksContext.Provider></NarrationCacheContext.Provider>;
}

/** Prepare only issued text while the pupil reads. No playback or future answers. */
export function useNarrationPreparation(source: NarrationSource | null, paragraphs: string[], { wholeLesson = true }: { wholeLesson?: boolean } = {}) {
  const cache = useContext(NarrationCacheContext);
  const bookmarks=useContext(PlaybackBookmarksContext);
  const sessionId = source?.sessionId, revision = source?.revision, text = JSON.stringify(paragraphs);
  useFocusEffect(useCallback(() => {
    if (!cache || !sessionId || revision === undefined || !JSON.parse(text).some((part: string) => part.trim())) return;
    let active = true, generation = 0;
    let foreground = AppState.currentState !== 'background' && AppState.currentState !== 'inactive';
    let chosen: NarrationChoice | undefined;
    const leases = new Set<ReturnType<NarrationCache['acquire']>>();
    const controls = new Set<AbortController>();
    const stop = () => { ++generation; leases.forEach(lease => lease.release()); leases.clear(); controls.forEach(control => control.abort()); controls.clear();void bookmarks?.flush(); };
    const prepareFuture = (voice: NarrationVoice) => {
      if (!wholeLesson) return;
      const control = new AbortController(); controls.add(control);
      // Private future scripts stay on the server; a question reply needs only its two voices.
      void prepareLessonMedia({ sessionId, revision }, voice, control.signal).catch(() => {})
        .finally(() => controls.delete(control));
    };
    const begin = async () => {
      stop(); const id = generation;
      const saved = chosen || await readNarrationVoice();
      if (!active || generation !== id) return;
      const selected = chosen || saved;
      chosen = selected;
      if (!isNarrationVoice(selected)) return;
      prepareFuture(selected);
      // Warm both versions of the currently issued script. The shared bounded
      // render/cache joins server preparation instead of synthesizing duplicates.
      const voices = [selected, ...NARRATION_VOICES.map(option => option.id).filter(voice => voice !== selected)];
      await Promise.allSettled(voices.map(async voice => {
        const lease = cache.acquire({ sessionId, revision }, JSON.parse(text), voice, true);
        leases.add(lease);
        await lease.promise;
      }));
    };
    if (foreground) void begin();
    const listener = AppState.addEventListener('change', state => {
      const next = state === 'active';
      if (next === foreground) return;
      foreground = next;
      if (foreground) void begin(); else stop();
    });
    const unsubscribe = subscribeNarrationVoice(voice => {
      const wasDevice = chosen === 'device';
      chosen = voice;
      if (!isNarrationVoice(voice)) { stop(); return; }
      if (foreground) {
        if (wasDevice) { void begin(); return; }
        // Both current assets already have leases. Keep the alternate download
        // alive when preference changes; only change the server's priority.
        prepareFuture(voice);
      }
    });
    return () => { active = false; stop(); listener.remove(); unsubscribe(); };
  }, [cache, sessionId, revision, text, wholeLesson,bookmarks]));
}
