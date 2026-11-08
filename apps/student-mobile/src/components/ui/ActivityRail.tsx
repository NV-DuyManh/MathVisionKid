import React, { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Platform, StyleSheet, View, type ViewStyle } from 'react-native';
import { COLORS } from '../../constants/theme';

/** Activity only: no invented percentage or remaining time. */
export function ActivityRail({ label = 'Đang xử lý', style }: { label?: string; style?: ViewStyle }) {
  const [motion] = useState(() => new Animated.Value(0));
  const [reduced, setReduced] = useState(true), [width, setWidth] = useState(0);
  const [foreground, setForeground] = useState(AppState.currentState !== 'background' && AppState.currentState !== 'inactive');
  useEffect(() => {
    let mounted = true;
    void AccessibilityInfo.isReduceMotionEnabled().then(value => { if (mounted) setReduced(value); }).catch(() => {});
    const preference = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced);
    const app = AppState.addEventListener('change', state => setForeground(state === 'active'));
    return () => { mounted = false; preference.remove(); app.remove(); };
  }, []);
  useEffect(() => {
    motion.setValue(0);
    if (reduced || !foreground || !width) return;
    const animation = Animated.loop(Animated.timing(motion, {
      toValue: 1, duration: 1400, easing: Easing.linear, useNativeDriver: Platform.OS !== 'web', isInteraction: false,
    }));
    animation.start();
    return () => { animation.stop(); motion.stopAnimation(); };
  }, [motion, reduced, foreground, width]);
  return <View style={[styles.track, style]} onLayout={event => setWidth(event.nativeEvent.layout.width)}
    accessibilityRole="progressbar" accessibilityLabel={label} accessibilityState={{ busy: true }} aria-busy>
    <Animated.View style={[styles.bar, { width: width * .3, transform: [{ translateX: !reduced && foreground
      ? motion.interpolate({ inputRange: [0, 1], outputRange: [-width * .3, width] }) : width * .35 }] }]} />
  </View>;
}
const styles = StyleSheet.create({
  track: { width: 110, height: 8, borderRadius: 4, backgroundColor: '#E8E1FB', overflow: 'hidden', alignSelf: 'center', marginVertical: 12 },
  bar: { height: '100%', borderRadius: 4, backgroundColor: COLORS.primary },
});
