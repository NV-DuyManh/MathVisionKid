import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { downloadNarration, NarrationSource } from './narrationApi';
import { saveNarration } from './narrationFile';
import { AudioPlayback } from './AudioPlayback';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { NARRATION_PROGRESS_STEPS } from './narration';
import { NARRATION_VOICES, NarrationVoice, readNarrationVoice, saveNarrationVoice } from './narrationVoices';

type Props = { scope: string; source: NarrationSource; paragraphs: string[]; disabled?: boolean; compact?: boolean; onFinished?: () => void };
type VoiceKeyEvent = Parameters<NonNullable<React.ComponentProps<typeof Pressable>['onKeyDown']>>[0];
export function LessonNarration(props: Props) {
  return <Narration key={JSON.stringify([props.scope, props.source, props.paragraphs, props.disabled])} {...props} />;
}
function Narration({ source, paragraphs, disabled = false, compact = false, onFinished }: Props) {
  const [uri, setUri] = useState(''), [error, setError] = useState(false), [attempt, setAttempt] = useState(0), [expanded, setExpanded] = useState(false);
  const [voice, setVoice] = useState<NarrationVoice | null>(null);
  const voiceButtons = useRef<(React.ElementRef<typeof View> | null)[]>([]);
  const transcriptId = useId();
  const playbackFailed = useCallback(() => setError(true), []);
  const sourceId = source.sessionId, revision = source.revision, text = JSON.stringify(paragraphs);
  useEffect(() => {
    let active = true;
    void readNarrationVoice().then(saved => { if (active) setVoice(saved); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (disabled || !voice) return;
    let active = true, asset: ReturnType<typeof saveNarration> | undefined;
    const controller = new AbortController();
    const listener = AppState.addEventListener('change', state => { if (state !== 'active' && !asset) { controller.abort(); if (active) setError(true); } });
    void downloadNarration({ sessionId: sourceId, revision }, JSON.parse(text), controller.signal, voice).then(bytes => {
      if (!active || controller.signal.aborted) return;
      asset = saveNarration(bytes); setUri(asset.uri);
    }).catch(() => { if (active && !controller.signal.aborted) setError(true); });
    return () => { active = false; controller.abort(); listener.remove(); asset?.dispose(); };
  }, [sourceId, revision, text, disabled, attempt, voice]);
  const chooseVoice = (selected: NarrationVoice) => {
    if (!voice || disabled || voice === selected) return;
    setUri(''); setError(false); setVoice(selected);
    void saveNarrationVoice(selected).catch(() => {});
  };
  return <View style={styles.stack}>
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
        <Ionicons name={voice === option.id ? 'radio-button-on' : 'radio-button-off'} size={19} color={voice === option.id ? COLORS.primaryDark : '#92829E'} accessible={false} />
        <View style={styles.voiceWords}><Text style={styles.voiceName}>{option.name}</Text><Text style={styles.voiceDescription}>{option.description}</Text></View>
      </Pressable>)}
    </View>
    {error ? <View style={styles.error} accessibilityLiveRegion="polite">
      <View style={styles.errorHeading}><Ionicons name="headset-outline" size={24} color="#8C6B3E" accessible={false} /><Text style={styles.errorTitle}>Âm thanh chưa sẵn sàng</Text></View>
      <Text style={styles.errorText}>Em vẫn có thể đọc lời giảng bên dưới, hoặc thử tải lại nhé.</Text>
      <AppButton title="Tải lại lời giảng" variant="secondary" onPress={() => { setUri(''); setError(false); setAttempt(value => value + 1); }} />
    </View> : uri ? <AudioPlayback key={uri} uri={uri} title={compact ? 'Lời giải thích' : 'Nghe giảng'} subtitle="Kéo để chọn đoạn muốn nghe" onFinished={onFinished} onError={playbackFailed} preparationSteps={NARRATION_PROGRESS_STEPS} />
      : disabled ? <Text style={styles.link}>Đang chờ bài học</Text> : <View style={styles.preparing}>
        <Text style={styles.preparingTitle}>Chuẩn bị lời giảng</Text>
        <TaskProgress steps={NARRATION_PROGRESS_STEPS} activeStep={voice ? 1 : 0} />
      </View>}
    <Pressable accessibilityRole="button" accessibilityLabel="Đọc lời giảng chi tiết" accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? transcriptId : undefined}
      style={({ pressed }) => [styles.transcript, pressed && { opacity: .65 }]} onPress={() => setExpanded(value => !value)}>
      <Ionicons name="reader-outline" size={18} color="#786A89" accessible={false} /><Text style={styles.link}>Xem lời giảng</Text><Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color="#786A89" accessible={false} />
    </Pressable>
    {expanded ? <View nativeID={transcriptId} style={styles.words}>{paragraphs.map((part, index) => <MathText key={index} style={styles.body}>{part}</MathText>)}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 10 }, transcript: { minHeight: 44, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 8 },
  preparing: { padding: 16, gap: 14, borderRadius: 18, backgroundColor: '#FCFAFF', borderWidth: 1, borderColor: '#E8DFF3' },
  preparingTitle: { fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  voices: { flexDirection: 'row', gap: 10 },
  voice: { flex: 1, minHeight: 52, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 14, borderWidth: 1, borderColor: '#E4DAEE', backgroundColor: '#FFF', flexDirection: 'row', alignItems: 'center', gap: 8 },
  voiceSelected: { borderColor: '#9773D3', backgroundColor: '#F3ECFC' }, voiceWords: { flex: 1 },
  voiceName: { fontFamily: FONTS.bold, fontSize: 13, lineHeight: 18, color: COLORS.textPrimary },
  voiceDescription: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 16, color: '#786A89' },
  link: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: '#786A89' }, words: { backgroundColor: '#FCFAFF', borderRadius: 16, padding: 14, gap: 10 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  error: { gap: 12, padding: 18, borderRadius: 22, borderWidth: 1, borderColor: '#EDDFC9', backgroundColor: '#FFFAF2' },
  errorHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 }, errorTitle: { flex: 1, fontFamily: FONTS.bold, fontSize: 16, lineHeight: 24, color: '#675047' },
  errorText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#675047' },
});
