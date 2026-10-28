import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Animated, AppState, Easing, Platform, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS } from '../../constants/theme';

export type TaskProgressProps = { steps: readonly string[]; activeStep?: number; complete?: boolean; percent?: number;
  detail?: string; timeoutSeconds?: number; onTimeout?: () => void; onComplete?: () => void };

/** MFILM-style visual estimate: creep below 85%, finish only on real readiness.
 * Server milestones are a lower bound. Timeout is never a denominator. */
export function TaskProgress({ steps, activeStep = 0, complete = false, percent, detail, timeoutSeconds = 45, onTimeout, onComplete }: TaskProgressProps) {
  const [started] = useState(Date.now);
  const [clock, setClock] = useState({ seconds: 0, percentage: Number.isFinite(percent) ? Math.max(0, Math.min(99, Math.floor(percent!))) : 6 });
  const [width, setWidth] = useState(0), [reduceMotion, setReduceMotion] = useState(true);
  const [foreground, setForeground] = useState(AppState.currentState !== 'background' && AppState.currentState !== 'inactive');
  const [motion] = useState(() => new Animated.Value(0));
  const completion = useRef(onComplete), timeout = useRef(onTimeout), notifiedTimeout = useRef(false), notifiedComplete = useRef(false);
  useEffect(() => { completion.current = onComplete; timeout.current = onTimeout; }, [onComplete, onTimeout]);
  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then(value => { if (mounted) setReduceMotion(value); }).catch(() => {});
    const preference = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    const app = AppState.addEventListener('change', state => setForeground(state === 'active'));
    return () => { mounted = false; preference.remove(); app.remove(); };
  }, []);
  useEffect(() => {
    if (complete || !foreground) return;
    const tick = () => {
      const elapsed = Math.max(0, (Date.now() - started) / 1000);
      const reported = Number.isFinite(percent) ? Math.min(99, Math.max(0, Math.floor(percent!))) : 0;
      setClock(previous => {
        const estimate = elapsed >= timeoutSeconds ? previous.percentage : Math.floor(6 + 79 * (1 - Math.exp(-elapsed / 8)));
        const next = { seconds: Math.floor(elapsed), percentage: Math.max(previous.percentage, reported, estimate) };
        return next.seconds === previous.seconds && next.percentage === previous.percentage ? previous : next;
      });
    };
    tick();
    const timer = setInterval(tick, 250);
    return () => clearInterval(timer);
  }, [started, complete, foreground, percent, timeoutSeconds]);
  const expired = !complete && clock.seconds >= timeoutSeconds;
  useEffect(() => {
    if (expired && !notifiedTimeout.current) { notifiedTimeout.current = true; timeout.current?.(); }
  }, [expired]);
  const percentage = complete ? 100 : clock.percentage;
  useEffect(() => {
    if (reduceMotion || !foreground || expired) { motion.setValue(percentage); return; }
    const animation = Animated.timing(motion, { toValue: percentage, duration: complete ? 180 : 350,
      easing: complete ? Easing.out(Easing.cubic) : Easing.linear, useNativeDriver: Platform.OS !== 'web' });
    animation.start();
    return () => animation.stop();
  }, [percentage, complete, reduceMotion, foreground, expired, motion]);
  useEffect(() => {
    if (!complete) { notifiedComplete.current = false; return; }
    const timer = setTimeout(() => {
      if (!notifiedComplete.current) { notifiedComplete.current = true; completion.current?.(); }
    }, reduceMotion ? 0 : 220);
    return () => clearTimeout(timer);
  }, [complete, reduceMotion]);
  if (!steps.length) return null;
  const current = Number.isFinite(activeStep) ? Math.min(steps.length - 1, Math.max(0, Math.floor(activeStep))) : 0;
  const summary = complete ? 'Đã sẵn sàng' : `Bước ${current + 1}/${steps.length} · ${steps[current]}`;
  const accessibleSummary = `${summary} · ${complete ? '' : 'Ước tính '}${percentage}%`;
  return <View style={styles.stack}>
    <View style={styles.summary}>
      <View style={styles.current}>
        {complete ? <Text style={styles.ready} accessible={false}>✓</Text> : <ActivityIndicator size="small" color={expired ? '#A55D30' : COLORS.primary} animating={foreground && !expired && !reduceMotion} />}
        <View style={styles.currentWords}><Text style={styles.stepCount}>{complete ? 'HOÀN TẤT' : `BƯỚC ${current + 1} / ${steps.length}`}</Text>
          <Text style={styles.currentName}>{expired ? 'Chờ lâu hơn dự kiến' : complete ? 'Đã sẵn sàng' : steps[current]}</Text></View>
      </View>
      <View style={styles.amount}><Text style={styles.percentage}>{percentage}%</Text>
        {!complete ? <Text style={styles.estimate}>Ước tính</Text> : null}</View>
    </View>
    <View style={styles.track} onLayout={event => setWidth(event.nativeEvent.layout.width)} accessibilityRole="progressbar" accessibilityLabel="Tiến độ chuẩn bị"
      accessibilityState={{ busy: !complete }} aria-busy={!complete}
      accessibilityValue={{ min: 0, max: 100, now: percentage, text: accessibleSummary }}
      aria-valuemin={0} aria-valuemax={100} aria-valuenow={percentage} aria-valuetext={accessibleSummary}>
      <Animated.View style={[styles.fill, { transform: [{ translateX: motion.interpolate({ inputRange: [0, 100], outputRange: [-width, 0] }) }], opacity: width ? 1 : 0 }]}>
        <LinearGradient colors={['#9877FF', '#7754F4', '#6842E8']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.gradient} />
      </Animated.View>
    </View>
    <View style={styles.timingRow}><Text style={styles.timing}>{complete ? 'Đã hoàn tất' : `Đã chờ ${clock.seconds}s`}</Text>
      {!complete ? <Text style={styles.limit}>Thời gian chờ tối đa {timeoutSeconds}s</Text> : null}</View>
    {expired || detail ? <Text style={[styles.detail, expired && styles.expired]} accessibilityLiveRegion="polite">{expired ? 'Chưa hoàn tất trong thời gian chờ. Em thử lại hoặc dùng cách khác nhé.' : detail}</Text> : null}
    <View style={styles.list}>
      {steps.map((step, index) => {
        const done = complete || index < current, working = !complete && index === current;
        const status = done ? 'Đã xong' : working ? 'Đang làm' : 'Sắp tới';
        return <View key={`${index}:${step}`} style={styles.milestone} accessible accessibilityLabel={`${step}. ${status}`}>
          <View style={[styles.number, done && styles.numberDone, working && styles.numberCurrent]}>
            <Text style={[styles.numberText, done && styles.check, working && styles.activeText]}>{done ? '✓' : index + 1}</Text>
          </View>
          <Text style={[styles.name, (done || working) && styles.activeText]}>{step}</Text>
        </View>;
      })}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  stack: { width: '100%', gap: 12 }, summary: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  current: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 }, currentWords: { flex: 1, gap: 2 },
  stepCount: { fontFamily: FONTS.bold, fontSize: 10, lineHeight: 15, letterSpacing: .8, color: COLORS.primaryDark },
  currentName: { fontFamily: FONTS.bold, fontSize: 14, lineHeight: 21, color: COLORS.textPrimary },
  amount: { alignItems: 'flex-end' }, percentage: { fontFamily: FONTS.extraBold, fontSize: 24, lineHeight: 29, color: COLORS.primaryDark, fontVariant: ['tabular-nums'] },
  estimate: { fontFamily: FONTS.medium, fontSize: 10, lineHeight: 15, color: COLORS.textSecondary }, ready: { color: COLORS.primaryDark, fontSize: 22 },
  track: { height: 7, borderRadius: 4, overflow: 'hidden', backgroundColor: '#E9E3FC' },
  fill: { width: '100%', height: '100%', borderRadius: 4, overflow: 'hidden' }, gradient: { flex: 1 },
  timingRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' },
  timing: { fontFamily: FONTS.semiBold, fontSize: 11, lineHeight: 17, color: COLORS.textSecondary, fontVariant: ['tabular-nums'] },
  limit: { fontFamily: FONTS.regular, fontSize: 10, lineHeight: 17, color: COLORS.textSecondary },
  detail: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 17, color: COLORS.textSecondary }, expired: { color: '#874323' },
  list: { flexDirection: 'row', gap: 10, paddingTop: 2 }, milestone: { flex: 1, alignItems: 'flex-start', gap: 6 },
  number: { width: 20, height: 20, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0ECF8' },
  numberDone: { backgroundColor: '#7754F4' }, numberCurrent: { backgroundColor: '#E6DCFF', borderColor: '#7754F4', borderWidth: 1 },
  numberText: { fontFamily: FONTS.bold, fontSize: 10, color: COLORS.textMuted }, check: { color: '#FFF' },
  name: { fontFamily: FONTS.semiBold, fontSize: 10, lineHeight: 15, color: COLORS.textSecondary }, activeText: { color: COLORS.primaryDark },
});
