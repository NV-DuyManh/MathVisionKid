import React, { useCallback, useContext, useEffect, useId, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { NarrationProgress, NarrationSource, NARRATION_WAIT_SECONDS } from './narrationApi';
import { getPreparedNarrationAsset } from './narrationCache';
import { NarrationCacheContext } from './NarrationPreparation';
import { saveNarration } from './narrationFile';
import { AudioPlayback } from './AudioPlayback';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { NARRATION_PROGRESS_STEPS } from './narration';
import { NARRATION_VOICES, NarrationVoice, readNarrationVoice, saveNarrationVoice } from './narrationVoices';
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
  const [uri, setUri] = useState(''), [error, setError] = useState(''), [attempt, setAttempt] = useState(0), [expanded, setExpanded] = useState(false);
  const [voice, setVoice] = useState<NarrationVoice | null>(null);
  const [progress, setProgress] = useState<NarrationProgress | null>(null);
  const [deviceVoice, setDeviceVoice] = useState(false);
  const [offlineFallback, setOfflineFallback] = useState(false);
  const [audioReady, setAudioReady] = useState(false), [preparationDone, setPreparationDone] = useState(false);
  const readyDeadline = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playbackStarted = useRef(0), readinessLogged = useRef(false);
  const playbackReady = useCallback(() => {
    if (readyDeadline.current) clearTimeout(readyDeadline.current);
    if (__DEV__ && !readinessLogged.current) console.info('[narration-latency]', { stage: 'player-ready', elapsedMs: Date.now()-playbackStarted.current });
    readinessLogged.current = true; setAudioReady(true);
  }, []);
  const voiceButtons = useRef<(React.ElementRef<typeof View> | null)[]>([]);
  const transcriptId = useId();
  const sourceId = source.sessionId, revision = source.revision, text = JSON.stringify(paragraphs);
  const playbackFailed = useCallback(() => {
    if (readyDeadline.current) clearTimeout(readyDeadline.current);
    if (voice) cache?.forget({ sessionId: sourceId, revision, ...(offlineFallback ? { useFallback: true } : {}) }, JSON.parse(text), voice);
    setError('Đã nhận âm thanh nhưng trình phát chưa mở được. Em thử tải lại hoặc dùng giọng trên thiết bị nhé.');
  }, [cache, sourceId, revision, text, voice, offlineFallback]);
  useEffect(() => {
    let active = true;
    void readNarrationVoice().then(saved => { if (active) setVoice(saved); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (disabled || !voice || deviceVoice) return;
    playbackStarted.current = Date.now(); readinessLogged.current = false;
    let active = true, asset: ReturnType<typeof saveNarration> | undefined;
    const controller = new AbortController();
    const audioSource = { sessionId: sourceId, revision, ...(offlineFallback ? { useFallback: true } : {}) };
    const watchdog = setTimeout(() => { controller.abort(); if (active) setError('Đã hết thời gian chờ lời giảng. Em có thể thử lại hoặc dùng giọng trên thiết bị.'); }, NARRATION_WAIT_SECONDS*1000);
    readyDeadline.current = watchdog;
    const listener = AppState.addEventListener('change', state => { if (state !== 'active' && !asset) { controller.abort(); if (active) setError('Đã dừng tải khi em rời màn hình. Em bấm tải lại khi sẵn sàng nhé.'); } });
    void getPreparedNarrationAsset(cache, audioSource, JSON.parse(text), controller.signal, voice, update => {
      if (active && !controller.signal.aborted) setProgress(update);
    }).then(prepared => {
      if (!active || controller.signal.aborted) { prepared.dispose(); return; }
      asset = prepared; setUri(asset.uri);
    }).catch((failure: unknown) => {
      clearTimeout(watchdog);
      if (!active || controller.signal.aborted) return;
      const error = failure as { code?: string; response?: { status?: number } } | null;
      const status = error?.response?.status;
      setError(status === 409 || status === 410 ? 'Phiên của bước này đã thay đổi. Em đóng lời giảng và mở lại bài học nhé.'
        : error?.code === 'ERR_NETWORK' ? 'Chưa kết nối được để tải giọng đọc. Em kiểm tra kết nối rồi thử lại nhé.'
        : status === 503 ? 'Chưa tạo xong giọng đọc lúc này. Em bấm Tải lại lời giảng để tiếp tục nhé.'
        : 'Chưa tạo hoặc tải được lời giảng. Em vẫn có thể đọc phần chữ, thử lại hoặc dùng giọng trên thiết bị.');
    });
    return () => { active = false; clearTimeout(watchdog); controller.abort(); listener.remove(); asset?.dispose(); };
  }, [sourceId, revision, text, disabled, attempt, voice, deviceVoice, offlineFallback, cache]);
  const chooseVoice = (selected: NarrationVoice) => {
    if (!voice || disabled || (voice === selected && !deviceVoice && !offlineFallback)) return;
    setUri(''); setError(''); setProgress(null); setVoice(selected); setDeviceVoice(false); setOfflineFallback(false);
    setAudioReady(false); setPreparationDone(false);
    void saveNarrationVoice(selected).catch(() => {});
  };
  return <View style={styles.stack}>
    <View style={styles.voiceHeading}><Text style={styles.voiceEyebrow}>GIỌNG ĐỒNG HÀNH</Text><Ionicons name="volume-medium-outline" size={15} color="#755C9A" accessible={false} /></View>
    <View accessibilityRole="radiogroup" accessibilityLabel="Chọn giọng đọc" style={styles.voices}>
      {NARRATION_VOICES.map((option, index) => <Pressable key={option.id} ref={node => { voiceButtons.current[index] = node; }} accessibilityRole="radio" accessibilityLabel={`${option.name}, ${option.description.toLowerCase()}`}
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
        {!smallVoice ? <View style={[styles.voiceAvatar, index === 1 && styles.voiceAvatarFemale]} accessible={false}><Text style={[styles.voiceInitials, index === 1 && styles.voiceInitialsFemale]}>{index === 0 ? 'NM' : 'HM'}</Text></View> : null}
        <View style={styles.voiceWords}><Text style={styles.voiceName}>{option.name}</Text><Text style={styles.voiceDescription}>{option.description}</Text></View>
        <Ionicons name={voice === option.id ? 'checkmark-circle' : 'ellipse-outline'} size={17} color={voice === option.id ? '#7046DD' : '#92829E'} accessible={false} />
      </Pressable>)}
    </View>
    {deviceVoice ? <DeviceNarration paragraphs={paragraphs} onFinished={onFinished} /> : error ? <View style={styles.error} accessibilityLiveRegion="polite">
      <View style={styles.errorHeading}><Ionicons name="headset-outline" size={24} color="#8C6B3E" accessible={false} /><Text style={styles.errorTitle}>Âm thanh chưa sẵn sàng</Text></View>
      <Text style={styles.errorText}>{error}</Text>
      <AppButton title="Tải lại lời giảng" variant="secondary" onPress={() => { setUri(''); setError(''); setProgress(null); setAudioReady(false); setPreparationDone(false); setAttempt(value => value + 1); }} />
      {!offlineFallback ? <AppButton title="Dùng giọng dự phòng (âm sắc khác)" variant="ghost" onPress={() => { setUri(''); setError(''); setProgress(null); setAudioReady(false); setPreparationDone(false); setOfflineFallback(true); }} /> : null}
      <AppButton title="Dùng giọng đọc trên thiết bị" variant="ghost" onPress={() => setDeviceVoice(true)} />
    </View> : disabled ? <Text style={styles.link}>Đang chờ bài học</Text> : <>
      {!preparationDone ? <View style={styles.preparing}>
        <Text style={styles.preparingTitle}>Chuẩn bị lời giảng</Text>
        <TaskProgress key={`${voice}:${attempt}:${offlineFallback}`} steps={NARRATION_PROGRESS_STEPS} activeStep={uri ? 2 : voice ? 1 : 0} percent={uri ? 95 : voice ? Math.max(10, Math.min(90, progress?.percent || 0)) : 0} timeoutSeconds={NARRATION_WAIT_SECONDS}
          complete={audioReady} onComplete={() => setPreparationDone(true)}
          detail={audioReady ? undefined : uri ? 'Đã nhận âm thanh. Đang mở lời giảng.' : offlineFallback ? 'Đang tạo giọng Việt dự phòng theo lựa chọn của em.' : progress?.totalChunks ? `Đã tạo ${progress.completedChunks}/${progress.totalChunks} đoạn giọng đọc.` : 'Đang chuẩn bị đúng giọng em đã chọn.'} />
      </View> : null}
      {uri ? <AudioPlayback key={uri} uri={uri} title={compact ? 'Lời giải thích' : 'Nghe giảng'} subtitle="Kéo để chọn đoạn muốn nghe" onFinished={onFinished} onError={playbackFailed} onReady={playbackReady} hideUntilReady /> : null}
      {uri && offlineFallback ? <Text style={styles.link}>Đang dùng giọng Việt dự phòng. Âm sắc có thể khác giọng em đã chọn; em vẫn tua và nghe lại được.</Text> : null}
    </>}
    <Pressable accessibilityRole="button" accessibilityLabel="Đọc lời giảng chi tiết" accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? transcriptId : undefined}
      style={({ pressed }) => [styles.transcript, pressed && { opacity: .65 }]} onPress={() => setExpanded(value => !value)}>
      <Ionicons name="reader-outline" size={18} color="#786A89" accessible={false} /><Text style={styles.link}>Xem lời giảng</Text><Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color="#786A89" accessible={false} />
    </Pressable>
    {expanded ? <View nativeID={transcriptId} style={styles.words}>{paragraphs.map((part, index) => <MathText key={index} style={styles.body}>{part}</MathText>)}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 10 }, transcript: { minHeight: 44, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 8 },
  preparing: { padding: 16, gap: 14, borderRadius: 22, backgroundColor: '#FBF9FF', borderWidth: 1, borderColor: '#E8DFF3' },
  preparingTitle: { fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  voiceHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 2 }, voiceEyebrow: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 16, letterSpacing: 1, color: '#755C9A' },
  voices: { flexDirection: 'row', gap: 8 },
  voice: { flex: 1, minWidth: 0, minHeight: 58, paddingHorizontal: 9, paddingVertical: 9, borderRadius: 17, borderWidth: 1.5, borderColor: '#EBE5F3', backgroundColor: '#FFF', flexDirection: 'row', alignItems: 'center', gap: 6 },
  voiceSelected: { borderColor: '#A186EB', backgroundColor: '#F5F0FF' }, voiceWords: { flex: 1, minWidth: 0 },
  voiceAvatar: { width: 28, height: 32, borderRadius: 10, backgroundColor: '#E9DFFF', alignItems: 'center', justifyContent: 'center' }, voiceAvatarFemale: { backgroundColor: '#FAE7E8' },
  voiceInitials: { fontFamily: FONTS.extraBold, fontSize: 10, color: '#6741BB' }, voiceInitialsFemale: { color: '#A04C6C' },
  voiceName: { fontFamily: FONTS.bold, fontSize: 13, lineHeight: 18, color: COLORS.textPrimary },
  voiceDescription: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 16, color: '#786A89' },
  link: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: '#786A89' }, words: { backgroundColor: '#FCFAFF', borderRadius: 16, padding: 14, gap: 10 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  error: { gap: 12, padding: 18, borderRadius: 22, borderWidth: 1, borderColor: '#EDDFC9', backgroundColor: '#FFFAF2' },
  errorHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 }, errorTitle: { flex: 1, fontFamily: FONTS.bold, fontSize: 16, lineHeight: 24, color: '#675047' },
  errorText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#675047' },
});
