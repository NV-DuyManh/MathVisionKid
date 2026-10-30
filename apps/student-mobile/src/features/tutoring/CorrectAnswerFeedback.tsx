import React, { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Platform, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FONTS } from '../../constants/theme';

const COLORS = ['#7055F6', '#F59E0B', '#10B981', '#3B82F6', '#EC4899'];
const PIECES = Array.from({ length: 18 }, (_, index) => ({
  x: Math.cos(index * 2.4) * (48 + index * 4), y: -34 - (index % 5) * 13,
  turn: `${index % 2 ? -240 : 240}deg`, color: COLORS[index % COLORS.length],
}));

/** One small celebration; never moves the next task or intercepts a touch. */
export function CorrectAnswerFeedback({ message }: { message: string }) {
  const [motion] = useState(() => new Animated.Value(0));
  const [celebrating, setCelebrating] = useState(false);
  useEffect(() => {
    let active = true;
    let animation: Animated.CompositeAnimation | undefined;
    void AccessibilityInfo.isReduceMotionEnabled().then(reduced => {
      if (!active || reduced || AppState.currentState === 'background' || AppState.currentState === 'inactive') return;
      setCelebrating(true);
      animation = Animated.timing(motion, { toValue: 1, duration: 900, easing: Easing.out(Easing.cubic), useNativeDriver: Platform.OS !== 'web' });
      animation.start(() => { if (active) setCelebrating(false); });
    }).catch(() => {});
    const stop = () => { animation?.stop(); setCelebrating(false); };
    const preference = AccessibilityInfo.addEventListener('reduceMotionChanged', value => { if (value) stop(); });
    const app = AppState.addEventListener('change', value => { if (value !== 'active') stop(); });
    return () => { active = false; animation?.stop(); preference.remove(); app.remove(); };
  }, [motion]);
  return <View style={styles.banner} testID="correct-answer-feedback">
    <View style={styles.badge}><Ionicons name="checkmark" size={23} color="#24794E" accessible={false} /></View>
    <View style={styles.words}><Text style={styles.title}>{message || 'Em làm đúng rồi!'}</Text>
      <Text style={styles.caption}>Em xem lại bước vừa làm, rồi bấm tiếp tục nhé.</Text></View>
    {celebrating ? <View testID="correct-answer-celebration" style={styles.burst} pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      {PIECES.map((piece, index) => <Animated.View key={index} style={[styles.piece, { backgroundColor: piece.color,
        opacity: motion.interpolate({ inputRange: [0, .65, 1], outputRange: [1, 1, 0] }),
        transform: [{ translateX: motion.interpolate({ inputRange: [0, 1], outputRange: [0, piece.x] }) },
          { translateY: motion.interpolate({ inputRange: [0, .5, 1], outputRange: [0, piece.y, 44] }) },
          { rotate: motion.interpolate({ inputRange: [0, 1], outputRange: ['0deg', piece.turn] }) }] }]} />)}
    </View> : null}
  </View>;
}
const styles = StyleSheet.create({
  banner: { position: 'relative', flexDirection: 'row', gap: 12, padding: 14, borderRadius: 18, backgroundColor: '#ECF8F0', borderWidth: 1, borderColor: '#D0EBD9' },
  badge: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#D6F0DF' },
  words: { flex: 1, gap: 4 }, title: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23, color: '#216B45' },
  caption: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: '#466C56' },
  burst: { position: 'absolute', left: '50%', top: 28 }, piece: { position: 'absolute', width: 6, height: 10, borderRadius: 2 },
});
