import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import type { Voice } from 'expo-speech';
import { voicePreferences } from './voicePreferences';
import { DEFAULT_SPEECH_RATE, DEFAULT_SPEECH_VOICE, readSpeechPreferences, SPEECH_RATES } from './speechPreferences';
import * as Speech from './speechOutput';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppButton } from '../../components/ui/AppButton';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { narrationSegments, vietnameseVoices, voiceLabel } from './narration';
import { warmSpeechSegments } from './speechCache';

type Props = { scope: string; paragraphs: string[]; disabled?: boolean; compact?: boolean; onFinished?: () => void };

export function LessonNarration({ scope, paragraphs, disabled = false, compact = false, onFinished }: Props) {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceId, setVoiceId] = useState(DEFAULT_SPEECH_VOICE);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [part, setPart] = useState(0);
  const [finished, setFinished] = useState(false);
  const [message, setMessage] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [settings, setSettings] = useState(false);
  const [rate, setRate] = useState(DEFAULT_SPEECH_RATE);
  const [focused, setFocused] = useState('');
  const active = useRef(false), speaking = useRef(false), sequence = useRef(0), voiceLoad = useRef(0);
  const pendingStop = useRef<Promise<void> | null>(null);
  const mounted = useRef(false);
  const transcriptId = useId(), settingsId = useId();
  const textKey = JSON.stringify(paragraphs);
  const sourceKey = `${scope}:${textKey}`;
  const currentSource = useRef(sourceKey);
  const voice = voices.find(item => item.identifier === voiceId) || voices[0];

  const stop = useCallback(() => {
    sequence.current += 1;
    if (speaking.current) {
      const task = Speech.stop().catch(() => {});
      pendingStop.current = task;
      void task.then(() => { if (pendingStop.current === task) pendingStop.current = null; });
      speaking.current = false;
    }
    if (active.current) { setPlaying(false); setPreparing(false); }
  }, []);
  const loadVoices = useCallback(() => {
    const id = ++voiceLoad.current;
    return Promise.all([Speech.getAvailableVoicesAsync(), readSpeechPreferences()]).then(([available, saved]) => {
      if (mounted.current && id === voiceLoad.current) {
        setVoices(vietnameseVoices(available)); setVoiceId(saved.voiceId); setRate(saved.rate); setLoading(false);
      }
    }, () => {
      if (mounted.current && id === voiceLoad.current) { setVoices([]); setLoading(false); }
    });
  }, []);
  useEffect(() => {
    mounted.current = true; void loadVoices();
    return () => { mounted.current = false; voiceLoad.current += 1; };
  }, [loadVoices]);
  useFocusEffect(useCallback(() => {
    currentSource.current = sourceKey;
    active.current = !disabled; setPlaying(false); setPreparing(false); setFinished(false); setPart(0); setMessage(''); setExpanded(false);
    const subscription = AppState.addEventListener('change', state => { if (state !== 'active') stop(); });
    return () => { active.current = false; stop(); subscription.remove(); };
  }, [sourceKey, disabled, stop]));

  const play = (preview = false) => {
    if (!active.current || disabled || !voice || speaking.current) return;
    const chunks = narrationSegments(preview ? ['Chào em. Mình cùng tìm hiểu bài toán, từng bước nhé.'] : paragraphs);
    if (!chunks.length) return;
    void warmSpeechSegments(chunks, voice.identifier).catch(() => {});
    const id = ++sequence.current;
    speaking.current = true; setPlaying(true); setPreparing(true); setFinished(false); setMessage(''); setPart(0);
    const valid = () => active.current && sequence.current === id && currentSource.current === sourceKey;
    const fail = () => {
      if (!valid()) return;
      stop();
      setMessage('Chưa phát được lời giảng. Em thử nghe lại hoặc đọc lời giảng bên dưới nhé.');
    };
    const speak = (index: number) => {
      if (!valid()) return;
      if (index > 0) void warmSpeechSegments(chunks.slice(index), voice.identifier).catch(() => {});
      try {
        Speech.speak(chunks[index], { language: 'vi-VN', voice: voice.identifier, rate, pitch: 1,
          onStart: () => { if (valid()) setPreparing(false); },
          onDone: () => {
            if (!valid()) return;
            if (!preview) setPart(index + 1);
            if (index + 1 < chunks.length) { setPreparing(true); speak(index + 1); }
            else { speaking.current = false; setPlaying(false); setPreparing(false); setFinished(!preview); if (!preview) onFinished?.(); }
          },
          onStopped: () => { if (valid()) { speaking.current = false; setPlaying(false); setPreparing(false); } },
          onError: fail,
        });
      } catch { fail(); }
    };
    // A previous owned utterance was already stopped on scope/setting changes.
    if (Platform.OS !== 'web' && pendingStop.current) void pendingStop.current.then(() => speak(0));
    else speak(0);
  };
  const toggle = (label: string, open: boolean, id: string, action: () => void) => <Pressable
    accessibilityRole="button" accessibilityLabel={label} aria-expanded={open} aria-controls={id}
    accessibilityState={{ expanded: open }} onPress={action}
    onFocus={() => setFocused(label)} onBlur={() => setFocused('')}
    style={[styles.toggle, focused === label && styles.focused]}><Text style={styles.link}>{label}</Text>
  </Pressable>;
  if (compact) return <View style={styles.details}>
    <AppButton title={playing ? 'Dừng nghe giải thích' : 'Nghe giải thích'} variant="secondary"
      disabled={disabled || loading || !voice || !paragraphs.length} onPress={() => playing ? stop() : play()} />
    {!loading && !voice ? <Text style={styles.caption}>Chưa tải được giọng đọc tiếng Việt. Em đọc phần chữ phía trên nhé.</Text> : null}
    {preparing ? <Text style={styles.caption} accessibilityLiveRegion="polite">Đang chuẩn bị lời đọc tiếng Việt…</Text> : null}
    {message ? <Text style={styles.notice} accessibilityRole="alert">{message}</Text> : null}
  </View>;
  const parts = narrationSegments(paragraphs).length;
  return <View style={styles.card}>
    <AppIllustration source={require('../../../assets/illustrations/star-listening.png')} style={styles.listeningArt} accessible={false} />
    <LinearGradient colors={['#6743D1', '#372385']} style={styles.player}>
      <View style={styles.playerTop}><Ionicons name="musical-notes" size={20} color="#C6B8FF" accessible={false} /><Text style={styles.playerTitle}>Nghe từng ý, hiểu từng bước</Text></View>
      <View style={styles.playerControls}>
        <View style={styles.wave} accessible={false} importantForAccessibility="no-hide-descendants" aria-hidden>{[7, 12, 20, 11, 26, 16, 9, 21, 30, 13, 23, 12].map((height, index) => <View key={index} style={[styles.waveBar, { height, opacity: playing ? .9 : .45 }]} />)}</View>
        <Pressable accessibilityRole="button" accessibilityLabel={playing ? 'Dừng nghe' : finished ? 'Nghe lại lời giảng' : 'Nghe giảng kỹ hơn'}
          disabled={disabled || loading || !voice || !paragraphs.length} accessibilityState={{ disabled: disabled || loading || !voice || !paragraphs.length }}
          onPress={() => playing ? stop() : play()} style={({ pressed }) => [styles.playButton, pressed && { opacity: .7 }]}>
          <Ionicons name={playing ? 'stop' : 'play'} size={25} color="#7751D8" accessible={false} />
        </Pressable>
        <View style={styles.wave} accessible={false} importantForAccessibility="no-hide-descendants" aria-hidden>{[15, 23, 10, 28, 12, 20, 8, 18, 25, 13, 19, 8].map((height, index) => <View key={index} style={[styles.waveBar, { height, opacity: playing ? .9 : .45 }]} />)}</View>
      </View>
      <View style={styles.audioProgress} accessible accessibilityRole="progressbar" accessibilityLabel="Các ý đã nghe" accessibilityValue={{ min: 0, max: parts, now: part }}>
        <View style={[styles.audioProgressFill, { width: (parts ? part / parts * 100 : 0) + '%' as any }]} />
      </View>
      <Text style={styles.playerStatus}>{preparing ? 'Đang chuẩn bị lời đọc' : playing ? 'Đang nghe' : finished ? 'Đã nghe xong' : 'Bấm để nghe'} · {part}/{parts} phần</Text>
    </LinearGradient>
    <Text style={styles.caption} accessibilityLiveRegion="polite">{preparing ? 'Đang chuẩn bị lời đọc tiếng Việt…' : playing ? 'Đang đọc lời giảng…' : finished ? 'Đã đọc xong lời giảng.'
      : loading ? 'Đang tìm giọng tiếng Việt…' : voice ? 'Em có thể nghe lại bất cứ lúc nào.'
        : 'Chưa tải được giọng đọc tiếng Việt. Em vẫn có thể đọc lời giảng chi tiết.'}</Text>
    {message ? <Text style={styles.notice} accessibilityRole="alert">{message}</Text> : null}
    {!loading && !voice ? <AppButton title="Tìm lại giọng đọc" variant="secondary" onPress={() => { setLoading(true); void loadVoices(); }} /> : null}
    <View style={styles.optionToggles}>{toggle('Giọng đọc và tốc độ', settings, settingsId, () => setSettings(value => !value))}
      {toggle('Đọc lời giảng chi tiết', expanded, transcriptId, () => setExpanded(value => !value))}</View>
    {settings ? <View nativeID={settingsId} style={styles.details}>
      <Text style={styles.label}>Giọng tiếng Việt</Text>
      {voices.map((item, index) => <Pressable key={item.identifier} accessibilityRole="button"
        accessibilityLabel={`Chọn ${voiceLabel(item, index)}`} aria-pressed={voice?.identifier === item.identifier}
        accessibilityState={Platform.OS === 'web' ? { disabled } : { selected: voice?.identifier === item.identifier, disabled }} disabled={disabled}
        onPress={() => { stop(); setVoiceId(item.identifier); void voicePreferences.set(JSON.stringify({ voiceId: item.identifier, rate })).catch(() => {}); }}
        onFocus={() => setFocused(item.identifier)} onBlur={() => setFocused('')}
        style={[styles.option, voice?.identifier === item.identifier && styles.selected, focused === item.identifier && styles.focused]}>
        <Text style={styles.body}>{voiceLabel(item, index)}{voice?.identifier === item.identifier ? ' · Đang chọn' : ''}</Text>
      </Pressable>)}
      <Text style={styles.label}>Tốc độ</Text>
      <View style={styles.controls}>{SPEECH_RATES.map(({ value, label }) => <Pressable key={label}
        accessibilityRole="button" accessibilityLabel={`Tốc độ ${label}`} aria-pressed={rate === value}
        accessibilityState={Platform.OS === 'web' ? { disabled } : { selected: rate === value, disabled }} disabled={disabled}
        onPress={() => { stop(); setRate(Number(value)); void voicePreferences.set(JSON.stringify({ voiceId: voice?.identifier, rate: Number(value) })).catch(() => {}); }} onFocus={() => setFocused(String(label))} onBlur={() => setFocused('')}
        style={[styles.option, styles.control, rate === value && styles.selected, focused === label && styles.focused]}>
        <Text style={styles.body}>{label} · {value.toFixed(2).replace('.', ',')}×</Text></Pressable>)}</View>
      <AppButton title="Nghe thử giọng" variant="secondary" disabled={disabled || !voice || playing} onPress={() => play(true)} />
    </View> : null}
    {expanded ? <View nativeID={transcriptId} style={styles.details}>
      {paragraphs.map((paragraph, index) => <MathText key={index} style={styles.body}>{paragraph}</MathText>)}
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { gap: 10 },
  listeningArt: { width: '100%', height: 140, alignSelf: 'center' },
  player: { borderRadius: 20, padding: 15, gap: 10, boxShadow: '0 5px 14px #6140BE24' },
  playerTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 }, playerTitle: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 18, color: '#F0E9FF' },
  playerControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  wave: { flex: 1, flexDirection: 'row', justifyContent: 'space-evenly', alignItems: 'center', height: 34 }, waveBar: { width: 3, borderRadius: 2, backgroundColor: '#BA9BFF' },
  playButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center', borderWidth: 4, borderColor: '#E0D1FF' },
  audioProgress: { height: 3, borderRadius: 2, backgroundColor: '#A58BCD60', overflow: 'hidden' }, audioProgressFill: { height: '100%', backgroundColor: '#E1D4FF' },
  playerStatus: { fontFamily: FONTS.semiBold, fontSize: 11, color: '#E0D4FA', textAlign: 'center' },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { fontSize: 19, lineHeight: 27, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  body: { fontSize: 15, lineHeight: 24, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  label: { fontSize: 15, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  caption: { fontSize: 12, lineHeight: 19, color: '#8A779F', fontFamily: FONTS.regular },
  controls: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 }, control: { flexGrow: 1, flexBasis: 130 },
  optionToggles: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  toggle: { flex: 1, minWidth: 105, minHeight: 44, padding: 7, borderWidth: 2, borderColor: '#EEE7F9', justifyContent: 'center', borderRadius: 12 },
  link: { fontSize: 13, lineHeight: 20, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  details: { gap: 12, padding: 12, borderRadius: 14, backgroundColor: COLORS.surface },
  option: { minHeight: 48, borderWidth: 2, borderColor: COLORS.border, borderRadius: 12, padding: 12, justifyContent: 'center' },
  selected: { borderColor: COLORS.primaryDark, backgroundColor: '#EEE8FF' },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  notice: { color: '#874323', fontSize: 14, lineHeight: 23, fontFamily: FONTS.medium },
});
