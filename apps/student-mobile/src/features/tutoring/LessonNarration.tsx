import React, { useCallback, useContext, useEffect, useId, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { NarrationProgress, NarrationSource, NARRATION_WAIT_SECONDS } from './narrationApi';
import { getPreparedNarrationAsset } from './narrationCache';
import { NarrationCacheContext, PlaybackBookmarksContext } from './NarrationPreparation';
import { type AudioCue } from './audioCues';
import { measureVoice } from './voiceMetrics';
import { saveNarration } from './narrationFile';
import { AudioPlayback } from './AudioPlayback';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { NARRATION_PROGRESS_STEPS } from './narration';
import { NARRATION_VOICES, NarrationVoice, currentNarrationVoice, readNarrationVoice, saveNarrationVoice } from './narrationVoices';
import { DeviceNarration } from './DeviceNarration';

type Props = { scope: string; source: NarrationSource; paragraphs: string[]; disabled?: boolean; compact?: boolean; onFinished?: () => void };
type VoiceKeyEvent = Parameters<NonNullable<React.ComponentProps<typeof Pressable>['onKeyDown']>>[0];
export function LessonNarration(props: Props) {
  return <Narration key={JSON.stringify([props.scope, props.source, props.paragraphs, props.disabled])} {...props} />;
}
function Narration({ source, paragraphs, disabled = false, compact = false, onFinished }: Props) {
  const { width, fontScale } = useWindowDimensions();
  const smallVoice = width < 370 || fontScale > 1.3;
  const cache = useContext(NarrationCacheContext);
  const bookmarks = useContext(PlaybackBookmarksContext);
  const [cues,setCues] = useState<AudioCue[]>([]), [initialPosition,setInitialPosition] = useState(0), [activeCue,setActiveCue] = useState(-1);
  const audioControl = useRef<{seekTo:(seconds:number)=>void}>(null);
  const [focusedCue,setFocusedCue]=useState<number|null>(null);
  const playerMeasure = useRef<ReturnType<typeof measureVoice> | null>(null);
  const [uri, setUri] = useState(''), [error, setError] = useState(''), [attempt, setAttempt] = useState(0), [expanded, setExpanded] = useState(false);
  const [voice, setVoice] = useState<NarrationVoice | null>(currentNarrationVoice);
  const [progress, setProgress] = useState<NarrationProgress | null>(null);
  const [deviceVoice, setDeviceVoice] = useState(false);
  const [audioReady, setAudioReady] = useState(false), [preparationDone, setPreparationDone] = useState(false);
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
  const voiceButtons = useRef<(React.ElementRef<typeof View> | null)[]>([]);
  const transcriptId = useId();
  const sourceId = source.sessionId, revision = source.revision, text = JSON.stringify(paragraphs);
  const bookmarkId = JSON.stringify([sourceId,voice,text]);
  const onPosition = useCallback((seconds:number,duration:number)=>{
    bookmarks?.set(bookmarkId,seconds,duration);
    const index=cues.findIndex(cue=>seconds>=cue.start&&seconds<cue.end);
    setActiveCue(previous=>previous===index?previous:index);
  },[bookmarks,bookmarkId,cues]);
  const playbackFailed = useCallback(() => {
    playerMeasure.current?.('failed');
    if (readyDeadline.current) clearTimeout(readyDeadline.current);
    if (preparationDelay.current) clearTimeout(preparationDelay.current);
    if (voice) cache?.forget({ sessionId: sourceId, revision }, JSON.parse(text), voice);
    setError('Tệp âm thanh chưa mở được. Em thử lại nhé.');
  }, [cache, sourceId, revision, text, voice]);
  useEffect(() => {
    let active = true;
    void readNarrationVoice().then(saved => { if (active) setVoice(saved); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (disabled || !voice || deviceVoice) return;
    playbackStarted.current = Date.now(); readinessLogged.current = false;
    let active = true, interrupted = false, asset: ReturnType<typeof saveNarration> | undefined;
    const displayTimer = setTimeout(() => { if (active) setShowPreparation(true); }, 180);
    preparationDelay.current = displayTimer;
    const controller = new AbortController();
    const audioSource = { sessionId: sourceId, revision };
    const watchdog = setTimeout(() => { controller.abort(); if (active) setError('Đã hết thời gian chờ. Em thử lại nhé.'); }, NARRATION_WAIT_SECONDS*1000);
    readyDeadline.current = watchdog;
    const listener = AppState.addEventListener('change', state => {
      if (!active) return;
      if (state !== 'active' && !asset && !controller.signal.aborted) {
        interrupted = true; clearTimeout(watchdog); clearTimeout(displayTimer); controller.abort();
        setError('Đã tạm dừng tải khi em rời màn hình.');
      } else if (state === 'active' && interrupted) {
        interrupted = false; setError(''); setProgress(null); setAudioReady(false); setPreparationDone(false); setShowPreparation(false);
        setAttempt(value => value + 1);
      }
    });
    void getPreparedNarrationAsset(cache, audioSource, JSON.parse(text), controller.signal, voice, update => {
      if (active && !controller.signal.aborted) setProgress(update);
    }).then(async prepared => {
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
  }, [sourceId, revision, text, disabled, attempt, voice, deviceVoice, cache, bookmarks, bookmarkId]);
  const chooseVoice = (selected: NarrationVoice) => {
    if (!voice || disabled || (voice === selected && !deviceVoice)) return;
    setUri(''); setError(''); setProgress(null); setVoice(selected); setDeviceVoice(false);
    setAudioReady(false); setPreparationDone(false); setShowPreparation(false);
    void saveNarrationVoice(selected).catch(() => {});
  };
  const retry = () => {
    setDeviceVoice(false); setUri(''); setError(''); setProgress(null);
    setAudioReady(false); setPreparationDone(false); setShowPreparation(false); setAttempt(value => value + 1);
  };
  return <View style={styles.stack}>
    <View style={styles.voiceHeading}><Text style={styles.voiceEyebrow}>GIỌNG ĐỒNG HÀNH</Text><Ionicons name="volume-medium-outline" size={15} color="#755C9A" accessible={false} /></View>
    <View accessibilityRole="radiogroup" accessibilityLabel="Chọn giọng đọc" style={styles.voices}>
      {NARRATION_VOICES.map((option, index) => <Pressable key={option.id} ref={node => { voiceButtons.current[index] = node; }} accessibilityRole="radio" accessibilityLabel={option.name}
        accessibilityState={{ checked: voice === option.id, disabled: !voice || disabled }} disabled={!voice || disabled}
        aria-checked={voice === option.id} aria-disabled={!voice || disabled}
        {...(Platform.OS === 'web' ? { tabIndex: voice === option.id ? 0 : -1, onKeyDown: (event: VoiceKeyEvent) => {
          const key = event.nativeEvent.key;
          if (!voice || disabled || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(key)) return;
          event.preventDefault();
          const next = key === 'Home' ? 0 : key === 'End' ? NARRATION_VOICES.length - 1 : (index + 1) % NARRATION_VOICES.length;
          chooseVoice(NARRATION_VOICES[next].id); voiceButtons.current[next]?.focus();
        } } : {})}
        style={({ pressed }) => [styles.voice, voice === option.id && styles.voiceSelected, pressed && { opacity: .7 }]}
        onPress={() => chooseVoice(option.id)}>
        {!smallVoice ? <View style={[styles.voiceAvatar, index === 1 && styles.voiceAvatarFemale]} accessible={false}><Ionicons name="volume-medium-outline" size={21} color={index === 0 ? '#7046DD' : '#B7647C'} /></View> : null}
        <View style={styles.voiceWords}><Text style={styles.voiceName}>{option.name}</Text></View>
        <Ionicons name={voice === option.id ? 'checkmark-circle' : 'ellipse-outline'} size={17} color={voice === option.id ? '#7046DD' : '#92829E'} accessible={false} />
      </Pressable>)}
    </View>
    {deviceVoice ? <DeviceNarration paragraphs={paragraphs} onFinished={onFinished} onReturn={retry} /> : error ? <RecoveryNotice
      title="Chưa mở được giọng đọc" message={error} actions={[
        { label: 'Thử lại', accessibilityLabel: 'Tải lại lời giảng', icon: 'refresh-outline', onPress: retry },
        { label: 'Giọng thiết bị', accessibilityLabel: 'Dùng giọng đọc trên thiết bị', onPress: () => setDeviceVoice(true) },
      ]} /> : disabled ? <Text style={styles.link}>Đang chờ bài học</Text> : <>
      {!preparationDone ? <View testID="narration-preparation" style={[styles.preparing, !showPreparation && styles.hidden]} aria-hidden={!showPreparation} importantForAccessibility={showPreparation ? 'auto' : 'no-hide-descendants'}>
        <Text style={styles.preparingTitle}>Chuẩn bị lời giảng</Text>
        <TaskProgress compact key={`${voice}:${attempt}`} steps={NARRATION_PROGRESS_STEPS} activeStep={uri ? 2 : voice ? 1 : 0} percent={uri ? 95 : voice ? Math.max(10, Math.min(90, progress?.percent || 0)) : 0} timeoutSeconds={NARRATION_WAIT_SECONDS}
          complete={audioReady} onComplete={() => setPreparationDone(true)}
          detail={audioReady ? undefined : uri ? 'Đã nhận âm thanh. Đang mở lời giảng.' : progress?.retrying ? 'Đang thử lại, giữ nguyên giọng em đã chọn.' : progress?.totalChunks ? `Đã tạo ${progress.completedChunks}/${progress.totalChunks} đoạn giọng đọc.` : 'Đang chuẩn bị đúng giọng em đã chọn.'} />
      </View> : null}
      {uri ? <View testID="narration-player" style={(!audioReady || showPreparation && !preparationDone) && styles.hidden}
        aria-hidden={!audioReady || showPreparation && !preparationDone} importantForAccessibility={!audioReady || showPreparation && !preparationDone ? 'no-hide-descendants' : 'auto'}>
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
  voiceHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 2 }, voiceEyebrow: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 16, letterSpacing: 1, color: '#755C9A' },
  voices: { flexDirection: 'row', gap: 8 },
  voice: { flex: 1, minWidth: 0, minHeight: 58, paddingHorizontal: 9, paddingVertical: 9, borderRadius: 17, borderWidth: 1.5, borderColor: '#EBE5F3', backgroundColor: '#FFF', flexDirection: 'row', alignItems: 'center', gap: 6 },
  voiceSelected: { borderColor: '#A186EB', backgroundColor: '#F5F0FF' }, voiceWords: { flex: 1, minWidth: 0 },
  voiceAvatar: { width: 28, height: 32, borderRadius: 10, backgroundColor: '#E9DFFF', alignItems: 'center', justifyContent: 'center' }, voiceAvatarFemale: { backgroundColor: '#FAE7E8' },
  voiceName: { fontFamily: FONTS.bold, fontSize: 13, lineHeight: 18, color: COLORS.textPrimary },
  link: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: '#786A89' }, words: { backgroundColor: '#FCFAFF', borderRadius: 16, padding: 14, gap: 10 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
});
