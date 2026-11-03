import React, { useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { AppState, Platform } from 'react-native';
import { useNavigation } from 'expo-router';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { getAvailableVoicesAsync, speak, stop } from './speechOutput';
import { vietnameseVoices } from './narration';
import { preparePlaybackSession } from './playbackSession';
import { MediaTimeline } from './MediaTimeline';
import { devicePosition, deviceProgress, deviceTimeline, estimatedDeviceDuration, rememberDevicePace } from './deviceTimeline';
import type { AudioCue } from './audioCues';

type Props = { paragraphs: string[]; compact?: boolean; onFinished?: () => void; onReturn?: () => void;
  controlRef?: React.Ref<{ seekTo: (seconds: number) => void }>;
  onReady?: (cues: AudioCue[]) => void; onPosition?: (seconds: number, duration: number) => void };
type State = 'loading' | 'ready' | 'starting' | 'speaking' | 'paused' | 'ended' | 'failed' | 'unavailable';

/** Same controls as recorded voices. Device seeking restarts speech at a word, with estimated time. */
export function DeviceNarration(props: Props) {
  return <DevicePlayback key={JSON.stringify(props.paragraphs)} {...props} />;
}
function DevicePlayback({ paragraphs, compact, onFinished, onReturn, controlRef, onReady, onPosition }: Props) {
  const text = JSON.stringify(paragraphs);
  const timeline = useMemo(() => deviceTimeline(JSON.parse(text)), [text]);
  const characters = timeline.chunks.reduce((sum, chunk) => sum + chunk.text.length, 0);
  const [voice, setVoice] = useState(''), [state, setState] = useState<State>('loading');
  const [lookup, setLookup] = useState(0), [rate, setRate] = useState(1);
  const [displayTime, setDisplayTime] = useState(0), [displayDuration, setDisplayDuration] = useState(() => estimatedDeviceDuration('', characters));
  const generation = useRef(0), navigation = useNavigation(), active = useRef(false);
  const playing = useRef(false), current = useRef(0), scrubPlaying = useRef<boolean | null>(null);
  const spoken = useRef<number | null>(null), focused = useRef(true), foreground = useRef(AppState.currentState !== 'background' && AppState.currentState !== 'inactive');
  const watchdog = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const clock = useRef<number | undefined>(undefined);
  const callbacks = useRef({ onFinished, onReady, onPosition });
  useEffect(() => { callbacks.current = { onFinished, onReady, onPosition }; }, [onFinished, onReady, onPosition]);
  const stopClock = () => { if (clock.current !== undefined) cancelAnimationFrame(clock.current); clock.current = undefined; };
  const clearTimers = () => { clearTimeout(watchdog.current); stopClock(); };
  const publish = (seconds: number, report = true) => {
    current.current = seconds;
    if (report) callbacks.current.onPosition?.(seconds, timeline.duration);
  };
  const pause = () => {
    ++generation.current; clearTimers(); playing.current = false;
    if (active.current) callbacks.current.onPosition?.(spoken.current ?? current.current, timeline.duration);
    void stop().catch(() => {});
    if (active.current) setState(value => value === 'speaking' || value === 'starting' ? 'paused' : value);
  };
  useEffect(() => {
    active.current = true;
    let checking = true;
    const timer = setTimeout(() => { if (checking) { checking = false; setState('unavailable'); } }, 5000);
    void getAvailableVoicesAsync().then(voices => {
      if (!checking) return;
      const selected = vietnameseVoices(voices)[0];
      setVoice(selected?.identifier || ''); setState(selected ? 'ready' : 'unavailable');
      if (selected) setDisplayDuration(estimatedDeviceDuration(selected.identifier, characters));
      if (selected) callbacks.current.onReady?.(timeline.cues);
    }).catch(() => { if (checking) setState('unavailable'); }).finally(() => clearTimeout(timer));
    const blur = navigation.addListener('blur', () => { focused.current = false; scrubPlaying.current = null; pause(); });
    const focus = navigation.addListener('focus', () => { focused.current = true; });
    const listener = AppState.addEventListener('change', next => { foreground.current = next === 'active'; if (next !== 'active') { scrubPlaying.current = null; pause(); } });
    return () => { checking = false; active.current = false; pause(); clearTimeout(timer); blur(); focus(); listener.remove(); };
    // The script and lookup own this lifecycle; transient position/rate changes must not restart speech.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, lookup, timeline]);

  const seek = (seconds: number, resume = scrubPlaying.current ?? playing.current, nextRate = rate, preserveProgress = false) => {
    if (!voice || !active.current || !focused.current || !foreground.current) return;
    const id = ++generation.current, target = devicePosition(timeline, seconds);
    clearTimers(); scrubPlaying.current = null; playing.current = resume; spoken.current = target.time;
    publish(preserveProgress ? Math.max(current.current, target.time) : target.time);
    const displayedStart = preserveProgress ? displayTime : target.time / timeline.duration * displayDuration;
    setDisplayTime(displayedStart);
    const stopped = stop();
    const fail = () => {
      if (!active.current || id !== generation.current) return;
      ++generation.current; clearTimers(); playing.current = false; void stop().catch(() => {}); setState('failed');
    };
    if (!resume || target.index >= timeline.chunks.length) {
      playing.current = false; setState(target.time >= timeline.duration ? 'ended' : 'paused');
      void stopped.catch(fail); return;
    }
    setState('starting');
    let utterance = 0;
    let progress: ReturnType<typeof deviceProgress> | undefined, reportedAt = 0;
    let currentChunk = timeline.chunks[target.index];
    const next = (index: number, offset = 0) => {
      if (!active.current || id !== generation.current) return;
      const sequence = ++utterance;
      const valid = () => active.current && id === generation.current && sequence === utterance;
      clearTimeout(watchdog.current);
      if (index >= timeline.chunks.length) {
        stopClock();
        const actual = progress?.finish(performance.now());
        if (actual && actual > 0) {
          setDisplayTime(actual); setDisplayDuration(actual);
          if (target.time === 0 && !preserveProgress) rememberDevicePace(voice, characters, actual);
        }
        playing.current = false; publish(timeline.duration); setState('ended'); callbacks.current.onFinished?.(); return;
      }
      const chunk = timeline.chunks[index], secondsPerChar = (chunk.end - chunk.start) / chunk.text.length;
      currentChunk = chunk;
      const start = chunk.start + offset * secondsPerChar;
      spoken.current = start;
      watchdog.current = setTimeout(fail, 8000);
      try {
        speak(chunk.text.slice(offset), { voice, language: 'vi-VN', rate: .9 * nextRate,
          onStart: () => {
            if (!valid()) return;
            clearTimeout(watchdog.current); setState('speaking');
            watchdog.current = setTimeout(fail, 90000);
            spoken.current = null;
            if (progress) return;
            progress = deviceProgress(start, timeline.duration, nextRate, performance.now(), displayedStart / displayDuration * timeline.duration, displayDuration);
            const thisReading = () => active.current && id === generation.current;
            const tick = () => {
              if (!thisReading() || !progress) return;
              const now = performance.now();
              // Keep the fallback within the utterance the engine is speaking.
              // Otherwise a slow engine with no word events can resume in a future sentence.
              const estimate = progress.advance(now);
              publish(Math.max(currentChunk.start, Math.min(currentChunk.end - .001, estimate)), false);
              setDisplayTime(progress.elapsed); setDisplayDuration(progress.duration);
              // Paint with the display refresh; transcript/bookmarks need only 4 Hz.
              if (now - reportedAt >= 250) { reportedAt = now; callbacks.current.onPosition?.(spoken.current ?? current.current, timeline.duration); }
              clock.current = requestAnimationFrame(tick);
            };
            clock.current = requestAnimationFrame(tick);
          },
          onBoundary: (event: { charIndex: number }) => {
            if (!valid() || !Number.isFinite(event.charIndex)) return;
            const anchor = chunk.start + Math.max(offset, Math.min(chunk.text.length, offset + event.charIndex)) * secondsPerChar;
            spoken.current = Math.max(spoken.current ?? start, anchor);
            progress?.boundary(spoken.current, performance.now());
          },
          onDone: () => { if (valid()) { progress?.boundary(chunk.end, performance.now()); next(index + 1); } }, onError: () => { if (valid()) fail(); },
        });
      } catch { fail(); }
    };
    watchdog.current = setTimeout(fail, 8000);
    if (Platform.OS === 'web') {
      // Keep speech inside the user gesture on browsers with autoplay restrictions.
      void stopped.catch(fail); next(target.index, target.offset);
    } else {
      void stopped.then(() => {
        if (active.current && id === generation.current) return preparePlaybackSession();
      }).then(() => { if (active.current && id === generation.current) next(target.index, target.offset); }).catch(fail);
    }
  };
  useImperativeHandle(controlRef, () => ({ seekTo: seconds => seek(seconds, true) }));

  if (state === 'unavailable' || state === 'failed') return <RecoveryNotice
    title={state === 'unavailable' ? 'Chưa có giọng Việt trên thiết bị' : 'Giọng thiết bị chưa phát được'}
    message="Em vẫn có thể mở lời giảng để đọc."
    actions={[
      { label: 'Thử lại', accessibilityLabel: 'Thử lại giọng thiết bị', icon: 'refresh-outline', onPress: () => { if (voice) seek(spoken.current ?? current.current, true, rate, true); else { setState('loading'); setLookup(value => value + 1); } } },
      ...(onReturn ? [{ label: 'Giọng chính', accessibilityLabel: 'Quay lại giọng đã chọn', onPress: onReturn }] : []),
    ]} />;
  return <MediaTimeline title={compact ? 'Lời giải thích' : 'Nghe giảng'} compact={compact} subtitle="Kéo để chọn đoạn muốn nghe"
    currentTime={displayTime} duration={displayDuration} playing={state === 'speaking' || state === 'starting'}
    disabled={!voice || !timeline.duration} loading={state === 'loading'} estimatedTime
    statusLabel={state === 'starting' ? 'Đang mở giọng' : state === 'paused' ? 'Đã tạm dừng' : state === 'ended' ? 'Đã nghe xong' : undefined}
    onToggle={() => { if (playing.current) pause(); else if (current.current >= timeline.duration) seek(0, true); else seek(spoken.current ?? current.current, true, rate, true); }}
    onSeek={seconds => seek(displayDuration ? seconds / displayDuration * timeline.duration : 0)} onRestart={() => seek(0, true)}
    onScrubStart={() => { scrubPlaying.current = playing.current; pause(); }} rate={rate}
    onRate={value => { setRate(value); seek(spoken.current ?? current.current, playing.current, value, true); }} />;
}
