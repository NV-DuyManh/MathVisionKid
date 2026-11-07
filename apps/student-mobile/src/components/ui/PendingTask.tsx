import React, { useEffect, useState } from 'react';
import { AppState, StyleSheet, Text, View } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';
import { ActivityRail } from './ActivityRail';

/** Activity, not a percentage: the server has not reported how much work remains. */
export function PendingTask({ title, detail }: { title: string; detail: string }) {
  const [foreground, setForeground] = useState(AppState.currentState !== 'background');
  const [started] = useState(() => performance.now());
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const appState = AppState.addEventListener('change', state => setForeground(state === 'active'));
    return () => appState.remove();
  }, []);
  useEffect(() => {
    if (!foreground) return;
    const timer = setInterval(() => setSeconds(Math.floor((performance.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [foreground, started]);
  return <View style={styles.card} aria-busy={true}>
    <View style={styles.row}>
      <Text style={styles.title} accessibilityLiveRegion="polite">{title}</Text>
      <Text style={styles.time} accessibilityLabel={`Đã chờ ${seconds} giây`}>{seconds}s</Text>
    </View>
    <ActivityRail label={title} style={styles.track} />
    <Text style={styles.detail}>{detail}</Text>
  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 15, gap: 11, backgroundColor: '#F7F3FF', borderWidth: 1, borderColor: '#E6DDF8', borderRadius: 18 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, lineHeight: 21, color: COLORS.primaryDark },
  time: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark, fontVariant: ['tabular-nums'], backgroundColor: '#EEE5FF', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  track: { width: '100%', height: 5, marginVertical: 0, backgroundColor: '#E9DFF9' },
  detail: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: COLORS.textSecondary },
});
