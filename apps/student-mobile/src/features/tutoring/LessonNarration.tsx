import React, { useCallback, useEffect, useId, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { downloadNarration, NarrationSource } from './narrationApi';
import { saveNarration } from './narrationFile';
import { AudioPlayback } from './AudioPlayback';
import { MediaTimeline } from './MediaTimeline';

type Props = { scope: string; source: NarrationSource; paragraphs: string[]; disabled?: boolean; compact?: boolean; onFinished?: () => void };
export function LessonNarration(props: Props) {
  return <Narration key={JSON.stringify([props.scope, props.source, props.paragraphs, props.disabled])} {...props} />;
}
function Narration({ source, paragraphs, disabled = false, compact = false, onFinished }: Props) {
  const [uri, setUri] = useState(''), [error, setError] = useState(false), [attempt, setAttempt] = useState(0), [expanded, setExpanded] = useState(false);
  const transcriptId = useId();
  const playbackFailed = useCallback(() => setError(true), []);
  const sourceId = source.sessionId, revision = source.revision, text = JSON.stringify(paragraphs);
  useEffect(() => {
    if (disabled) return;
    let active = true, asset: ReturnType<typeof saveNarration> | undefined;
    const controller = new AbortController();
    const listener = AppState.addEventListener('change', state => { if (state !== 'active' && !asset) { controller.abort(); if (active) setError(true); } });
    void downloadNarration({ sessionId: sourceId, revision }, JSON.parse(text), controller.signal).then(bytes => {
      if (!active || controller.signal.aborted) return;
      asset = saveNarration(bytes); setUri(asset.uri);
    }).catch(() => { if (active && !controller.signal.aborted) setError(true); });
    return () => { active = false; controller.abort(); listener.remove(); asset?.dispose(); };
  }, [sourceId, revision, text, disabled, attempt]);
  return <View style={styles.stack}>
    {error ? <View style={styles.error} accessibilityLiveRegion="polite">
      <View style={styles.errorHeading}><Ionicons name="headset-outline" size={24} color="#8C6B3E" accessible={false} /><Text style={styles.errorTitle}>Âm thanh chưa sẵn sàng</Text></View>
      <Text style={styles.errorText}>Em vẫn có thể đọc lời giảng bên dưới, hoặc thử tải lại nhé.</Text>
      <AppButton title="Tải lại lời giảng" variant="secondary" onPress={() => { setUri(''); setError(false); setAttempt(value => value + 1); }} />
    </View> : uri ? <AudioPlayback key={uri} uri={uri} title={compact ? 'Lời giải thích' : 'Nghe giảng'} subtitle="Kéo để chọn đoạn muốn nghe" onFinished={onFinished} onError={playbackFailed} />
      : <MediaTimeline title={compact ? 'Lời giải thích' : 'Nghe giảng'} subtitle={disabled ? 'Đang chờ bài học' : 'Đang chuẩn bị âm thanh…'}
        duration={0} currentTime={0} playing={false} disabled loading={!disabled} onSeek={() => {}} onScrubStart={() => {}} onToggle={() => {}} />}
    <Pressable accessibilityRole="button" accessibilityLabel="Đọc lời giảng chi tiết" accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? transcriptId : undefined}
      style={({ pressed }) => [styles.transcript, pressed && { opacity: .65 }]} onPress={() => setExpanded(value => !value)}>
      <Ionicons name="reader-outline" size={18} color="#786A89" accessible={false} /><Text style={styles.link}>Xem lời giảng</Text><Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color="#786A89" accessible={false} />
    </Pressable>
    {expanded ? <View nativeID={transcriptId} style={styles.words}>{paragraphs.map((part, index) => <MathText key={index} style={styles.body}>{part}</MathText>)}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 10 }, transcript: { minHeight: 44, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 8 },
  link: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: '#786A89' }, words: { backgroundColor: '#FCFAFF', borderRadius: 18, padding: 17, gap: 12 },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 25, color: COLORS.textSecondary },
  error: { gap: 12, padding: 18, borderRadius: 22, borderWidth: 1, borderColor: '#EDDFC9', backgroundColor: '#FFFAF2' },
  errorHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 }, errorTitle: { flex: 1, fontFamily: FONTS.bold, fontSize: 16, lineHeight: 24, color: '#675047' },
  errorText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#675047' },
});
