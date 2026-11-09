import React, { useCallback, useContext, useEffect, useId, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { NarrationProgress, NarrationSource, NARRATION_WAIT_SECONDS } from './narrationApi';
import { getPreparedNarrationAsset, NARRATION_RENDER_POLICY } from './narrationCache';
import { NarrationCacheContext, PlaybackBookmarksContext } from './NarrationPreparation';
import { type AudioCue } from './audioCues';
import { measureVoice } from './voiceMetrics';
import { saveNarration } from './narrationFile';
import { AudioPlayback } from './AudioPlayback';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { NARRATION_PROGRESS_STEPS } from './narration';
import { DEFAULT_NARRATION_VOICE, isNarrationVoice, type NarrationChoice, type NarrationVoice, currentNarrationVoice, readNarrationVoice, saveNarrationVoice } from './narrationVoices';
import { DeviceNarration } from './DeviceNarration';
import { VoicePicker } from './VoicePicker';

type Props = { scope: string; source: NarrationSource; paragraphs: string[]; disabled?: boolean; compact?: boolean; onFinished?: () => void;
  audioLoader?: (voice: NarrationVoice, signal: AbortSignal) => Promise<Uint8Array> };
export function LessonNarration(props: Props) {
  return <Narration key={JSON.stringify([NARRATION_RENDER_POLICY, props.scope, props.source, props.paragraphs, props.disabled])} {...props} />;
}
function Narration({ source, paragraphs, disabled = false, compact = false, onFinished, audioLoader }: Props) {
  const cache = useContext(NarrationCacheContext);
  const bookmarks = useContext(PlaybackBookmarksContext);
  const [cues,setCues] = useState<AudioCue[]>([]), [initialPosition,setInitialPosition] = useState(0), [activeCue,setActiveCue] = useState(-1);
  const audioControl = useRef<{seekTo:(seconds:number)=>void}>(null);
  const [focusedCue,setFocusedCue]=useState<number|null>(null);
  const playerMeasure = useRef<ReturnType<typeof measureVoice> | null>(null);
  const [uri, setUri] = useState(''), [error, setError] = useState(''), [attempt, setAttempt] = useState(0), [expanded, setExpanded] = useState(false);
  const [voice, setVoice] = useState<NarrationChoice | null>(currentNarrationVoice);
  const [serverFallback, setServerFallback] = useState(false);
  const onlineVoice = useRef<NarrationVoice>(isNarrationVoice(voice) ? voice : DEFAULT_NARRATION_VOICE);
  const [progress, setProgress] = useState<NarrationProgress | null>(null);
  const deviceVoice = voice === 'device';
  const [audioReady, setAudioReady] = useState(false);
  const [showPreparation, setShowPreparation] = useState(false);
  const preparationDelay = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readyDeadline = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playbackStarted = useRef(0), readinessLogged = useRef(false);
  const playbackReady = useCallback(() => {
    if (readyDeadline.current) clearTimeout(readyDeadline.current);
    if (preparationDelay.current) clearTimeout(preparationDelay.current);
    if (__DEV__ && !readinessLogged.current) console.info('[narration-latency]', { stage: 'player-ready', elapsedMs: Date.now()-playbackStarted.current });
    readinessLogged.current = true; setAudioReady(true);
    playerMeasure.current?.('ready');
  }, []);
  const transcriptId = useId();
  const deviceReady = useCallback((points: AudioCue[]) => { setCues(points); setAudioReady(true); }, []);
  const sourceId = source.sessionId, revision = source.revision, text = JSON.stringify(paragraphs);
  const bookmarkId = JSON.stringify([sourceId, voice, text, ...(serverFallback ? ['server-fallback'] : [])]);
  const onPosition = useCallback((seconds:number,duration:number)=>{
    bookmarks?.set(bookmarkId,seconds,duration);
    const index=cues.findIndex(cue=>seconds>=cue.start&&seconds<cue.end);
    setActiveCue(previous=>previous===index?previous:index);
  },[bookmarks,bookmarkId,cues]);
  const playbackFailed = useCallback(() => {
    playerMeasure.current?.('failed');
    if (readyDeadline.current) clearTimeout(readyDeadline.current);
    if (preparationDelay.current) clearTimeout(preparationDelay.current);
    if (isNarrationVoice(voice)) cache?.forget({ sessionId: sourceId, revision, ...(serverFallback ? { useFallback: true } : {}) }, JSON.parse(text), voice);
    setError('Tệp âm thanh chưa mở được. Em thử lại nhé.');
  }, [cache, sourceId, revision, text, voice, serverFallback]);
  useEffect(() => {
    let active = true;
    void readNarrationVoice().then(saved => { if (active) setVoice(saved); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (disabled || !isNarrationVoice(voice)) return;
    playbackStarted.current = Date.now(); readinessLogged.current = false;
    let active = true, interrupted = false, asset: Awaited<ReturnType<typeof saveNarration>> | undefined;
    const displayTimer = setTimeout(() => { if (active) setShowPreparation(true); }, 180);
    preparationDelay.current = displayTimer;
    const controller = new AbortController();
    const audioSource = { sessionId: sourceId, revision, ...(serverFallback ? { useFallback: true } : {}) };
    const watchdog = setTimeout(() => { controller.abort(); if (active) setError('Đã hết thời gian chờ. Em thử lại nhé.'); }, NARRATION_WAIT_SECONDS*1000);
    readyDeadline.current = watchdog;
    const listener = AppState.addEventListener('change', state => {
      if (!active) return;
      if (state !== 'active' && !asset && !controller.signal.aborted) {
        interrupted = true; clearTimeout(watchdog); clearTimeout(displayTimer); controller.abort();
        setError('Đã tạm dừng tải khi em rời màn hình.');
      } else if (state === 'active' && interrupted) {
        interrupted = false; setError(''); setProgress(null); setAudioReady(false); setShowPreparation(false);
        setAttempt(value => value + 1);
      }
    });
    const preparedAudio = audioLoader && !cache ? audioLoader(voice, controller.signal).then(saveNarration) : getPreparedNarrationAsset(cache, audioSource, JSON.parse(text), controller.signal, voice, update => {
      if (active && !controller.signal.aborted) setProgress(update);
    });
    void preparedAudio.then(async prepared => {
      if (!active || controller.signal.aborted) { prepared.dispose(); return; }
      asset = prepared;
      const position = await bookmarks?.get(bookmarkId) || 0;
      if (!active || controller.signal.aborted) return;
      setInitialPosition(position);setCues(prepared.cues?.length===JSON.parse(text).length?(prepared.cues||[]):[]);
      playerMeasure.current=measureVoice('player',voice);
      setUri(asset.uri);
    }).catch((failure: unknown) => {
      clearTimeout(watchdog); clearTimeout(displayTimer);
      if (!active || controller.signal.aborted) return;
      const error = failure as { code?: string; response?: { status?: number } } | null;
      const status = error?.response?.status;
      setError(status === 409 || status === 410 ? 'Phiên của bước này đã thay đổi. Em đóng lời giảng và mở lại bài học nhé.'
        : error?.code === 'ERR_NETWORK' ? 'Chưa có kết nối mạng. Em kiểm tra lại nhé.'
        : status === 503 ? 'Giọng đọc đang bận. Em thử lại nhé.'
        : 'Em thử lại hoặc nghe bằng giọng thiết bị nhé.');
    });
    return () => { active = false; clearTimeout(watchdog); clearTimeout(displayTimer); controller.abort(); listener.remove(); asset?.dispose(); playerMeasure.current?.('cancelled');void bookmarks?.flush(); };
  }, [sourceId, revision, text, disabled, attempt, voice, cache, bookmarks, bookmarkId, audioLoader, serverFallback]);
  const chooseVoice = (selected: NarrationChoice) => {
    if (!voice || disabled || voice === selected) return;
    if (isNarrationVoice(voice)) onlineVoice.current = voice;
    if (isNarrationVoice(selected)) onlineVoice.current = selected;
    setServerFallback(false);
    setUri(''); setError(''); setProgress(null); setVoice(selected);
    setCues([]); setActiveCue(-1);
    setAudioReady(false); setShowPreparation(false);
    void saveNarrationVoice(selected).catch(() => {});
  };
  const retry = () => {
    setUri(''); setError(''); setProgress(null);
    setAudioReady(false); setShowPreparation(false); setAttempt(value => value + 1);
  };
  const changeFallback = (enabled: boolean) => {
    setServerFallback(enabled);
    retry();
  };
  const preparationDetail = uri ? 'Đã nhận âm thanh. Đang mở lời giảng.'
    : progress?.retrying ? serverFallback ? 'Đang thử lại giọng Việt dự phòng.' : 'Đang thử lại, giữ nguyên giọng em đã chọn.'
    : progress?.totalChunks ? `Đã tạo ${progress.completedChunks}/${progress.totalChunks} đoạn giọng đọc.`
    : serverFallback ? 'Đang chuẩn bị giọng Việt dự phòng.' : 'Đang chuẩn bị đúng giọng em đã chọn.';
  return <View style={styles.stack}>
    <VoicePicker value={voice} disabled={disabled || serverFallback} onChange={chooseVoice} />
    {serverFallback ? <View style={styles.currentWords} accessibilityLiveRegion="polite">
      <Text style={styles.body}>Đang dùng giọng Việt dự phòng.</Text>
      <Pressable accessibilityRole="button" onPress={() => changeFallback(false)} style={styles.transcript}>
        <Text style={styles.link}>Quay lại giọng đã chọn</Text>
      </Pressable>
    </View> : null}
    {disabled ? <Text style={styles.link}>Đang chờ bài học</Text> : deviceVoice ? <DeviceNarration paragraphs={paragraphs} compact={compact} controlRef={audioControl} onReady={deviceReady} onPosition={onPosition} onFinished={onFinished} onReturn={() => chooseVoice(onlineVoice.current)} /> : error ? <RecoveryNotice
      title="Chưa mở được giọng đọc" message={error} actions={[
        { label: 'Thử lại', accessibilityLabel: 'Tải lại lời giảng', icon: 'refresh-outline', onPress: retry },
        ...(!serverFallback && !audioLoader ? [{ label: 'Dùng giọng Việt dự phòng', onPress: () => changeFallback(true) }] : []),
        { label: 'Giọng có sẵn', accessibilityLabel: 'Dùng giọng đọc trên thiết bị', onPress: () => chooseVoice('device') },
    ]} /> : <>
      {!audioReady ? <View testID="narration-preparation" style={[styles.preparing, !showPreparation && styles.hidden]} aria-hidden={!showPreparation} importantForAccessibility={showPreparation ? 'auto' : 'no-hide-descendants'}>
        <Text style={styles.preparingTitle}>Chuẩn bị lời giảng</Text>
        <TaskProgress compact key={`${voice}:${attempt}`} steps={NARRATION_PROGRESS_STEPS} activeStep={uri ? 2 : voice ? 1 : 0} percent={uri ? 95 : voice ? Math.max(10, Math.min(90, progress?.percent || 0)) : 0} timeoutSeconds={NARRATION_WAIT_SECONDS}
          complete={audioReady}
          detail={audioReady ? undefined : preparationDetail} />
      </View> : null}
      {uri ? <View testID="narration-player" style={!audioReady && styles.hidden}
        aria-hidden={!audioReady} importantForAccessibility={!audioReady ? 'no-hide-descendants' : 'auto'}>
        <AudioPlayback key={uri} uri={uri} compact={compact} controlRef={audioControl} initialPosition={initialPosition} onPosition={onPosition} title={compact ? 'Lời giải thích' : 'Nghe giảng'} subtitle="Kéo để chọn đoạn muốn nghe" onFinished={onFinished} onError={playbackFailed} onReady={playbackReady} hideUntilReady />
      </View> : null}
    </>}
    <Pressable accessibilityRole="button" accessibilityLabel="Đọc lời giảng chi tiết" accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? transcriptId : undefined}
      style={({ pressed }) => [styles.transcript, pressed && { opacity: .65 }]} onPress={() => setExpanded(value => !value)}>
      <Ionicons name="reader-outline" size={18} color="#786A89" accessible={false} /><Text style={styles.link}>Xem lời giảng</Text><Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color="#786A89" accessible={false} />
    </Pressable>
    {audioReady&&cues.length>0&&!expanded&&activeCue>=0 ? <View style={styles.currentWords}><Text style={styles.voiceEyebrow}>LỜI GIẢNG THEO ĐOẠN</Text><MathText style={styles.body}>{paragraphs[activeCue]}</MathText></View> : null}
    {expanded ? <View nativeID={transcriptId} style={styles.words}>{paragraphs.map((part, index) => cues.length&&audioReady ? <Pressable key={index} accessibilityRole="button" accessibilityLabel={`Nghe đoạn ${index+1}: ${part}`} accessibilityState={{selected:activeCue===index}}
      onFocus={event=>{const target=event.currentTarget as unknown as {matches?:(selector:string)=>boolean};if(Platform.OS!=='web'||target.matches?.(':focus-visible'))setFocusedCue(index);}} onBlur={()=>setFocusedCue(null)} onPointerDown={()=>setFocusedCue(null)}
      onPress={()=>audioControl.current?.seekTo(cues[index].start)} style={[styles.cue,activeCue===index&&styles.currentWords,focusedCue===index&&styles.cueFocus]}><MathText style={styles.body}>{part}</MathText></Pressable> : <MathText key={index} style={styles.body}>{part}</MathText>)}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  cue: {minHeight:48,padding:10,borderRadius:12},currentWords:{padding:12,gap:5,borderRadius:14,backgroundColor:'#EEE7FC',borderLeftWidth:3,borderLeftColor:'#7950DA'},
  cueFocus:{outlineWidth:2,outlineOffset:2,outlineStyle:'solid',outlineColor:'#6C43C4'},
  hidden: { display: 'none' },
  stack: { gap: 10 }, transcript: { minHeight: 44, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 8 },
  preparing: { padding: 16, gap: 14, borderRadius: 22, backgroundColor: '#FBF9FF', borderWidth: 1, borderColor: '#E8DFF3' },
  preparingTitle: { fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  voiceEyebrow: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 16, letterSpacing: 1, color: '#755C9A' },
  link: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: '#786A89' }, words: { backgroundColor: '#FCFAFF', borderRadius: 16, padding: 14, gap: 10 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
});
