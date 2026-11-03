import React, { useState } from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import Slider from './MediaSlider';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS } from '../../constants/theme';

export const mediaTime = (seconds: number) => `${Math.floor(Math.max(0, seconds) / 60)}:${String(Math.floor(Math.max(0, seconds) % 60)).padStart(2, '0')}`;
const skipSeconds = 5;
type Props = { title: string; subtitle?: string; currentTime: number; duration: number; playing: boolean; disabled?: boolean; loading?: boolean; compact?: boolean;
  onToggle: () => void; onSeek: (seconds: number) => void; onScrubStart: () => void; onRestart?: () => void;
  playLabel?: string; pauseLabel?: string; restartLabel?: string; rate?: number; onRate?: (rate: number) => void;
  estimatedTime?: boolean; statusLabel?: string };

/** Shared time controls for narration and recorded questions. */
export function MediaTimeline({ title, subtitle, currentTime, duration, playing, disabled = false, loading = false, compact = false, onToggle, onSeek, onScrubStart, onRestart,
  playLabel = 'Phát lời giảng', pauseLabel = 'Tạm dừng lời giảng', restartLabel = 'Nghe lại từ đầu', rate = 1, onRate, estimatedTime = false, statusLabel }: Props) {
  const [dragging, setDragging] = useState<number | null>(null);
  const [focused, setFocused] = useState('');
  const { width, fontScale } = useWindowDimensions();
  const statusBelow = width < 390 || fontScale > 1.2;
  const total = Number.isFinite(duration) && duration > 0 ? duration : 0;
  const position = Math.max(0, Math.min(dragging ?? currentTime, total));
  const blocked = disabled || loading || !total;
  const focus = (control: string) => ({
    onFocus: (event: Parameters<NonNullable<React.ComponentProps<typeof Pressable>['onFocus']>>[0]) => {
      const target = event?.currentTarget as unknown as { matches?: (selector: string) => boolean };
      setFocused(Platform.OS !== 'web' || target?.matches?.(':focus-visible') ? control : '');
    },
    onBlur: () => setFocused(''), onPointerDown: () => setFocused(''),
  });
  const status = !compact ? <View style={[styles.statePill, playing && styles.statePillPlaying]}><View style={[styles.stateDot, playing && styles.stateDotPlaying]} accessible={false}/><Text accessibilityLiveRegion="polite" style={[styles.stateText, playing && styles.stateTextPlaying]}>{statusLabel || (loading ? 'Đang chuẩn bị' : playing ? 'Đang phát' : disabled ? 'Chưa sẵn sàng' : total ? 'Sẵn sàng' : 'Đang đọc thời lượng')}</Text></View> : null;
  return <View testID="media-timeline" style={[styles.card, compact && styles.compactCard]} aria-busy={loading}>
    <View style={styles.heading}><View style={styles.badge}><Ionicons name="headset-outline" size={21} color="#7046DD" accessible={false} /></View>
      <View style={styles.flex}><Text style={styles.title}>{title}</Text>{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}</View>
      {!statusBelow ? status : null}
    </View>
    {statusBelow && status ? <View style={styles.stateRow}>{status}</View> : null}
    <View style={styles.timeline}>
      {/* A fixed native range prevents quantization shifts when an estimate changes. */}
      <Slider accessibilityLabel={`Tua ${title.toLowerCase()}`} accessibilityValue={{ min: 0, max: total, now: position, text: `${estimatedTime ? 'Ước tính ' : ''}${mediaTime(position)} trên ${mediaTime(total)}` }}
        style={styles.slider} minimumValue={0} maximumValue={1} step={0.0001} value={total ? position / total : 0} disabled={blocked} tapToSeek
        minimumTrackTintColor={COLORS.primary} maximumTrackTintColor={COLORS.primaryLight} thumbTintColor={COLORS.primaryDark}
        onSlidingStart={() => { setDragging(position); onScrubStart(); }} onValueChange={value => setDragging(value * total)}
        onSlidingComplete={value => { setDragging(null); onSeek(Math.max(0, Math.min(value * total, total))); }} />
      <View style={styles.times}><Text style={styles.time}>{mediaTime(position)}</Text><Text style={styles.time}>{mediaTime(total)}</Text></View>
      {estimatedTime ? <Text style={styles.subtitle}>Thời gian ước tính · Tua theo vị trí lời đọc</Text> : null}
    </View>
    <View style={[styles.controls, compact && styles.compactControls]}>
      <Pressable {...focus('back')} accessibilityRole="button" accessibilityLabel={`Lùi ${skipSeconds} giây`} disabled={blocked} accessibilityState={{ disabled: blocked }} onPress={() => onSeek(Math.max(0, currentTime - skipSeconds))}
        style={({ pressed }) => [styles.skip, focused === 'back' && styles.focused, (blocked || pressed) && styles.dimmed]}><Ionicons name="play-back-outline" size={22} color="#625074" accessible={false} /><Text style={styles.skipText}>−{skipSeconds}s</Text></Pressable>
      <Pressable {...focus('play')} accessibilityRole="button" accessibilityLabel={playing ? pauseLabel : playLabel} disabled={blocked} accessibilityState={{ disabled: blocked }} onPress={onToggle}
        style={({ pressed }) => [styles.play, compact && styles.compactPlay, focused === 'play' && styles.focused, blocked && styles.dimmed, pressed && !blocked && styles.pressed]}><LinearGradient colors={[COLORS.primary, COLORS.primaryDark]} start={{x:0,y:0}} end={{x:1,y:1}} style={styles.playFill}>{loading ? <ActivityIndicator color="#FFFFFF" accessibilityLabel="Đang tải nội dung" /> : <Ionicons name={playing ? 'pause' : 'play'} size={compact ? 24 : 29} color="#FFFFFF" accessible={false} />}</LinearGradient></Pressable>
      <Pressable {...focus('forward')} accessibilityRole="button" accessibilityLabel={`Tiến ${skipSeconds} giây`} disabled={blocked} accessibilityState={{ disabled: blocked }} onPress={() => onSeek(Math.min(total, currentTime + skipSeconds))}
        style={({ pressed }) => [styles.skip, focused === 'forward' && styles.focused, (blocked || pressed) && styles.dimmed]}><Ionicons name="play-forward-outline" size={22} color="#625074" accessible={false} /><Text style={styles.skipText}>+{skipSeconds}s</Text></Pressable>
    </View>
    <View style={styles.footer}>
      <Pressable {...focus('restart')} accessibilityRole="button" accessibilityLabel={restartLabel} accessibilityState={{ disabled: blocked }} disabled={blocked} onPress={() => onRestart ? onRestart() : onSeek(0)} style={({ pressed }) => [styles.restart, focused === 'restart' && styles.focused, (blocked || pressed) && styles.dimmed]}>
        <Ionicons name="refresh-outline" size={16} color="#6F6080" accessible={false} /><Text style={styles.restartText}>Nghe lại</Text></Pressable>
      {onRate ? <Pressable {...focus('rate')} accessibilityRole="button" accessibilityLabel={`Tốc độ ${rate} lần. Bấm để đổi tốc độ`} accessibilityHint="Đổi giữa chậm, bình thường và nhanh" accessibilityState={{ disabled: blocked }} disabled={blocked}
        onPress={() => onRate(rate === 1 ? .8 : rate === .8 ? 1.2 : 1)} style={({ pressed }) => [styles.rate, focused === 'rate' && styles.focused, (blocked || pressed) && styles.dimmed]}><Ionicons name="speedometer-outline" size={16} color="#6F6080" accessible={false} /><Text style={styles.rateText}>{rate}×</Text></Pressable> : null}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  card: { padding: 18, paddingBottom: 12, borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: '#E4DCEF', gap: 6 },
  compactCard: { padding: 14, paddingBottom: 10, gap: 2 }, compactControls: { paddingVertical: 6 }, compactPlay: { width: 60, height: 60, borderRadius: 30, borderWidth: 4 },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 10 }, badge: { width: 40, height: 44, borderRadius: 15, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center' },
  flex: { flex: 1, minWidth: 0 }, title: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23, color: COLORS.textPrimary }, subtitle: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 17, color: COLORS.textSecondary, marginTop: 2 },
  stateRow: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingTop: 4, flexWrap: 'wrap' }, stateDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: '#8060BF' }, stateDotPlaying: { backgroundColor: '#27815D' },
  statePill: { flexDirection: 'row', alignItems: 'center', flexShrink: 1, gap: 5, paddingHorizontal: 8, paddingVertical: 5, borderRadius: 20, backgroundColor: '#F4F0FA' }, statePillPlaying: { backgroundColor: '#E8F5EE' },
  stateText: { flexShrink: 1, fontFamily: FONTS.bold, fontSize: 10, lineHeight: 16, color: '#61516F' }, stateTextPlaying: { color: '#23694F' },
  rate: { minWidth: 72, minHeight: 48, paddingHorizontal: 10, flexDirection: 'row', gap: 6, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#F6F3FB' }, rateText: { fontFamily: FONTS.bold, fontSize: 13, color: '#625074' },
  timeline: { marginTop: 3 }, slider: { width: '100%' as const, height: 48 }, times: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 2, marginTop: -4 },
  time: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.textSecondary, fontVariant: ['tabular-nums'] },
  controls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-evenly', paddingVertical: 12 },
  play: { width: 78, height: 78, borderRadius: 39, borderWidth: 5, borderColor: COLORS.primaryLight, backgroundColor: COLORS.primary },
  playFill: { flex: 1, borderRadius: 33, alignItems: 'center', justifyContent: 'center' }, pressed: { opacity: .8 },
  skip: { minWidth: 48, minHeight: 52, paddingHorizontal: 6, borderRadius: 16, backgroundColor: '#F6F3FB', alignItems: 'center', justifyContent: 'center', gap: 3 }, skipText: { fontFamily: FONTS.bold, fontSize: 11, color: '#625074' },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#EEE8F5', paddingTop: 8, marginTop: 4, gap: 8, flexWrap: 'wrap' },
  restart: { minHeight: 48, paddingHorizontal: 10, borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 }, restartText: { fontFamily: FONTS.bold, fontSize: 12, color: '#625074' }, dimmed: { opacity: .45 },
  focused: { outlineStyle: 'solid', outlineColor: '#261E45', outlineWidth: 2, outlineOffset: 3 },
});
