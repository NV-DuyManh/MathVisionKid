import React, { useState } from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import Slider from './MediaSlider';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { FONTS } from '../../constants/theme';

export const mediaTime = (seconds: number) => `${Math.floor(Math.max(0, seconds) / 60)}:${String(Math.floor(Math.max(0, seconds) % 60)).padStart(2, '0')}`;
type Props = { title: string; subtitle?: string; currentTime: number; duration: number; playing: boolean; disabled?: boolean; loading?: boolean; compact?: boolean;
  onToggle: () => void; onSeek: (seconds: number) => void; onScrubStart: () => void; onRestart?: () => void;
  playLabel?: string; pauseLabel?: string; restartLabel?: string; skipSeconds?: number; rate?: number; onRate?: (rate: number) => void };

/** Shared time controls for narration and recorded questions. */
export function MediaTimeline({ title, subtitle, currentTime, duration, playing, disabled = false, loading = false, compact = false, onToggle, onSeek, onScrubStart, onRestart,
  playLabel = 'Phát lời giảng', pauseLabel = 'Tạm dừng lời giảng', restartLabel = 'Nghe lại từ đầu', skipSeconds = 10, rate = 1, onRate }: Props) {
  const [dragging, setDragging] = useState<number | null>(null);
  const [focused, setFocused] = useState('');
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
  return <View testID="media-timeline" style={[styles.card, compact && styles.compactCard]} aria-busy={loading}>
    <View style={styles.heading}><View style={styles.badge}><Ionicons name="headset-outline" size={21} color="#7046DD" accessible={false} /></View>
      <View style={styles.flex}><Text style={styles.title}>{title}</Text>{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}</View>
    </View>
    {!compact ? <View style={styles.stateRow}><View style={[styles.statePill, playing && styles.statePillPlaying]}><View style={[styles.stateDot, playing && styles.stateDotPlaying]} /><Text accessibilityLiveRegion="polite" style={[styles.stateText, playing && styles.stateTextPlaying]}>{loading ? 'Đang chuẩn bị' : playing ? 'Đang phát' : disabled ? 'Chưa sẵn sàng' : total ? 'Sẵn sàng' : 'Đang đọc thời lượng'}</Text></View>
      </View> : null}
    <View style={styles.timeline}>
      <Slider accessibilityLabel={`Tua ${title.toLowerCase()}`} accessibilityValue={{ min: 0, max: total, now: position, text: `${mediaTime(position)} trên ${mediaTime(total)}` }}
        style={styles.slider} minimumValue={0} maximumValue={total || 1} value={position} disabled={blocked} tapToSeek
        minimumTrackTintColor="#7650E6" maximumTrackTintColor="#E4DDF3" thumbTintColor="#7650E6"
        onSlidingStart={() => { setDragging(position); onScrubStart(); }} onValueChange={setDragging}
        onSlidingComplete={value => { setDragging(null); onSeek(Math.max(0, Math.min(value, total))); }} />
      <View style={styles.times}><Text style={styles.time}>{mediaTime(position)}</Text><Text style={styles.time}>{mediaTime(total)}</Text></View>
    </View>
    <View style={[styles.controls, compact && styles.compactControls]}>
      <Pressable {...focus('back')} accessibilityRole="button" accessibilityLabel={`Lùi ${skipSeconds} giây`} disabled={blocked} accessibilityState={{ disabled: blocked }} onPress={() => onSeek(Math.max(0, currentTime - skipSeconds))}
        style={({ pressed }) => [styles.skip, focused === 'back' && styles.focused, (blocked || pressed) && styles.dimmed]}><Ionicons name="play-back-outline" size={22} color="#625074" accessible={false} /><Text style={styles.skipText}>−{skipSeconds}s</Text></Pressable>
      <Pressable {...focus('play')} accessibilityRole="button" accessibilityLabel={playing ? pauseLabel : playLabel} disabled={blocked} accessibilityState={{ disabled: blocked }} onPress={onToggle}
        style={({ pressed }) => [styles.play, compact && styles.compactPlay, focused === 'play' && styles.focused, blocked && styles.dimmed, pressed && !blocked && styles.pressed]}><LinearGradient colors={['#9265FF', '#6E42E2']} start={{x:0,y:0}} end={{x:1,y:1}} style={styles.playFill}>{loading ? <ActivityIndicator color="#FFFFFF" accessibilityLabel="Đang tải nội dung" /> : <Ionicons name={playing ? 'pause' : 'play'} size={compact ? 24 : 29} color="#FFFFFF" accessible={false} />}</LinearGradient></Pressable>
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
  card: { padding: 16, paddingBottom: 12, borderRadius: 24, backgroundColor: '#FCFAFF', borderWidth: 1, borderColor: '#E6DDF6', gap: 4 },
  compactCard: { padding: 13, paddingBottom: 10, gap: 1 }, compactControls: { paddingVertical: 6 }, compactPlay: { width: 58, height: 58, borderRadius: 29, borderWidth: 3 },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 10 }, badge: { width: 44, height: 44, borderRadius: 15, backgroundColor: '#EEE5FF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#E3D5FC' },
  flex: { flex: 1, minWidth: 0 }, title: { fontFamily: FONTS.extraBold, fontSize: 15, lineHeight: 22, color: '#261E45' }, subtitle: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 17, color: '#6F6080', marginTop: 1 },
  stateRow: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingTop: 10, flexWrap: 'wrap' }, stateDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#8060BF' }, stateDotPlaying: { backgroundColor: '#27815D' },
  statePill: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 9, backgroundColor: '#F0EAF9' }, statePillPlaying: { backgroundColor: '#E8F5EE' },
  stateText: { fontFamily: FONTS.bold, fontSize: 10, lineHeight: 16, color: '#61516F' }, stateTextPlaying: { color: '#23694F' },
  rate: { minWidth: 72, minHeight: 44, paddingHorizontal: 10, flexDirection: 'row', gap: 6, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#F1ECF8' }, rateText: { fontFamily: FONTS.bold, fontSize: 13, color: '#6F6080' },
  timeline: { marginTop: 3 }, slider: { width: '100%' as const, height: 48 }, times: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 2, marginTop: -4 },
  time: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#6F6080', fontVariant: ['tabular-nums'] },
  controls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-evenly', paddingVertical: 10 },
  play: { width: 76, height: 76, borderRadius: 38, borderWidth: 5, borderColor: '#EEE5FD', backgroundColor: '#7950DA' },
  playFill: { flex: 1, borderRadius: 33, alignItems: 'center', justifyContent: 'center' }, pressed: { opacity: .8 },
  skip: { minWidth: 48, minHeight: 48, borderRadius: 14, alignItems: 'center', justifyContent: 'center', gap: 2 }, skipText: { fontFamily: FONTS.bold, fontSize: 11, color: '#6F6080' },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#EDE6F6', paddingTop: 10, marginTop: 4, gap: 8, flexWrap: 'wrap' },
  restart: { minHeight: 44, paddingHorizontal: 11, borderRadius: 12, backgroundColor: '#F1ECF8', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 }, restartText: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#6F6080' }, dimmed: { opacity: .45 },
  focused: { outlineStyle: 'solid', outlineColor: '#261E45', outlineWidth: 2, outlineOffset: 3 },
});
