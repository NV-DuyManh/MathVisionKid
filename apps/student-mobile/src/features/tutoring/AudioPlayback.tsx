/* eslint-disable react-hooks/immutability -- Expo AudioPlayer exposes imperative native mute/volume setters, not React state. */
import React, { useEffect, useImperativeHandle, useRef, useState } from 'react';
import { AppState, Platform, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from 'expo-router';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { MediaTimeline } from './MediaTimeline';
import { preparePlaybackSession } from './playbackSession';
import { FONTS } from '../../constants/theme';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';

type Props = {
  controlRef?: React.Ref<{ seekTo: (seconds: number) => void }>; initialPosition?: number; onPosition?: (seconds: number, duration: number) => void;
  uri: string; title: string; subtitle?: string; durationHint?: number; question?: boolean; compact?: boolean; onFinished?: () => void; onError?: () => void; onReady?: () => void; hideUntilReady?: boolean; preparationSteps?: readonly string[];
};
export function AudioPlayback(props: Props) {
  const [attempt, setAttempt] = useState(0);
  return <Playback key={`${props.uri}:${attempt}`} {...props} onRetry={() => setAttempt(value => value + 1)} />;
}
function Playback({ uri, title, subtitle, durationHint = 0, question = false, compact = question, onFinished, onError, onReady, hideUntilReady = false, preparationSteps, onRetry, controlRef, initialPosition=0, onPosition }: Props & { onRetry: () => void }) {
  const player = useAudioPlayer(uri, { updateInterval: 200 });
  const status = useAudioPlayerStatus(player), navigation = useNavigation();
  const [notice, setNotice] = useState(''), [rate, setRate] = useState(1);
  const [loadExpired, setLoadExpired] = useState(false);
  const [positionReady, setPositionReady] = useState(!Number.isFinite(initialPosition)||initialPosition<=0);
  const restored = useRef(false);
  const [preparationVisible, setPreparationVisible] = useState(!status.isLoaded);
  const loadTimedOut = loadExpired && !status.isLoaded;
  const active = useRef(true), generation = useRef(0), scrubPlaying = useRef<boolean | null>(null);
  const watchdog = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearWatchdog = () => { if (watchdog.current) clearTimeout(watchdog.current); watchdog.current = null; };
  const finished = useRef(false), didPlay = useRef(false), complete = useRef(onFinished);
  const duration = Number.isFinite(status.duration) && status.duration > 0 ? status.duration : durationHint;
  const current = Math.max(0, Math.min(Number.isFinite(status.currentTime) ? status.currentTime : 0, duration));
  useEffect(() => { complete.current = onFinished; }, [onFinished]);
  useEffect(() => { if (status.error) onError?.(); }, [status.error, onError]);
  useEffect(() => { if (status.isLoaded && !status.error && positionReady) onReady?.(); }, [status.isLoaded, status.error, onReady, positionReady]);
  useEffect(()=>{
    if (!status.isLoaded || duration<=0 || restored.current) return;
    restored.current=true;
    if(!Number.isFinite(initialPosition)||initialPosition<=0)return;
    void player.seekTo(initialPosition>=duration-.3?0:initialPosition).catch(()=>{}).finally(()=>{if(active.current)setPositionReady(true);});
  },[status.isLoaded,initialPosition,duration,player]);
  useEffect(()=>{
    if (positionReady && status.isLoaded && !status.error) onPosition?.(Math.max(0,Math.min(player.currentTime,duration)),duration);
  },[current,duration,status.isLoaded,status.error,positionReady,onPosition,player]);
  useEffect(() => {
    if (status.isLoaded || status.error) return;
    const timer = setTimeout(() => { setLoadExpired(true); onError?.(); }, 12000);
    return () => clearTimeout(timer);
  }, [status.isLoaded, status.error, onError]);
  useEffect(() => {
    active.current = true;
    const invalidate = () => { ++generation.current; clearWatchdog(); };
    const pause = () => { invalidate(); scrubPlaying.current = null; player.pause(); };
    const blur = navigation.addListener('blur', pause);
    const listener = AppState.addEventListener('change', state => { if (state !== 'active') pause(); });
    return () => { active.current = false; invalidate(); blur(); listener.remove(); };
  }, [navigation, player]);
  useEffect(() => {
    if (status.playing) didPlay.current = true;
    if (status.didJustFinish && didPlay.current && !finished.current) { finished.current = true; complete.current?.(); }
  }, [status.playing, status.didJustFinish]);
  const play = async (id: number) => {
    if (Platform.OS !== 'web') await preparePlaybackSession();
    if (!active.current || generation.current !== id) return;
    player.muted = false;
    player.volume = 1; // Player gain only; the pupil's system volume stays unchanged.
    didPlay.current = true;
    const position = player.currentTime;
    player.play();
    clearWatchdog();
    watchdog.current = setTimeout(() => {
      watchdog.current = null;
      if (active.current && generation.current === id && player.currentTime <= position && !player.currentStatus.didJustFinish) {
        player.pause();
        setNotice('Chưa phát được âm thanh. Em bấm phát để thử lại nhé.');
      }
    }, 6000);
  };
  const seek = async (seconds: number, playAfter?: boolean) => {
    const id = ++generation.current, resume = playAfter ?? scrubPlaying.current ?? player.playing;
    scrubPlaying.current = null;
    try {
      setNotice(''); await player.seekTo(Math.max(0, Math.min(seconds, duration)));
      if (active.current && generation.current === id && resume) await play(id);
    } catch { if (active.current && generation.current === id) setNotice('Chưa phát được âm thanh. Em thử lại nhé.'); }
  };
  const toggle = async () => {
    clearWatchdog();
    if (player.playing) { ++generation.current; player.pause(); }
    else if (status.didJustFinish || current >= duration) void seek(0, true);
    else {
      const id = ++generation.current;
      setNotice('');
      try { await play(id); } catch { if (active.current && generation.current === id) setNotice('Chưa phát được âm thanh. Em thử lại nhé.'); }
    }
  };
  useImperativeHandle(controlRef,()=>({seekTo: seconds=>{if(status.isLoaded&&positionReady)void seek(seconds,true);}}));
  if (status.error || loadTimedOut) return onError ? null : <RecoveryNotice title={question ? 'Chưa mở được bản ghi' : 'Chưa mở được âm thanh'}
    message="Em thử tải lại tệp nhé." actions={[{ label: 'Thử lại', accessibilityLabel: question ? 'Tải lại bản ghi' : 'Tải lại âm thanh', icon: 'refresh-outline', onPress: onRetry }]} />;
  if (hideUntilReady && !status.isLoaded) return null;
  return <View style={styles.stack}>
    {preparationSteps && preparationVisible && !status.error && !loadTimedOut ? <TaskProgress steps={preparationSteps} activeStep={preparationSteps.length - 1} percent={95} complete={status.isLoaded} onComplete={() => setPreparationVisible(false)} timeoutSeconds={12} detail={status.isLoaded ? undefined : 'Đã nhận âm thanh. Đang mở tệp để em có thể phát và tua.'} /> : null}
    <MediaTimeline title={title} compact={compact} subtitle={loadTimedOut ? 'Chưa mở được âm thanh' : !status.isLoaded && !status.error ? 'Đang mở âm thanh…' : subtitle} currentTime={current} duration={duration} playing={status.playing} disabled={!status.isLoaded || Boolean(status.error) || loadTimedOut} loading={!status.isLoaded && !status.error && !loadTimedOut}
      playLabel={question ? 'Nghe lại câu hỏi vừa nói' : status.didJustFinish ? 'Nghe lại lời giảng' : 'Phát lời giảng'} pauseLabel={question ? 'Tạm dừng bản ghi' : 'Tạm dừng lời giảng'} skipSeconds={question ? 5 : 10}
      onToggle={toggle} onSeek={seconds => { void seek(seconds); }} onRestart={() => { void seek(0, true); }}
      onScrubStart={() => { scrubPlaying.current = player.playing; ++generation.current; clearWatchdog(); player.pause(); }}
      rate={rate} onRate={question ? undefined : value => { try { player.setPlaybackRate(value); setRate(value); setNotice(''); } catch { setNotice('Chưa đổi được tốc độ. Em vẫn có thể nghe ở tốc độ hiện tại.'); } }} />
    {notice ? <Text accessibilityRole="alert" style={styles.notice}>{notice}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({ stack: { gap: 10 }, notice: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#874323' } });
