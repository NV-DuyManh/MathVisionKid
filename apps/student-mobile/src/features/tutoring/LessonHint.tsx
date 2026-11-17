import React, { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';

/** One short hint at a time; the calculation and answer stay outside this panel. */
export function LessonHint({ text, level, count, busy, onPrevious, onNext, onClose, onExplain }: {
  text: string; level: number; count: number; busy: boolean; onPrevious?: () => void;
  onNext?: () => void; onClose: () => void; onExplain?: () => void;
}) {
  const [opacity] = useState(() => new Animated.Value(1));
  useEffect(() => {
    let active = true;
    let animation: Animated.CompositeAnimation | undefined;
    void AccessibilityInfo.isReduceMotionEnabled().then(reduced => {
      if (!active || reduced) return;
      opacity.setValue(0);
      animation = Animated.timing(opacity, { toValue: 1, duration: 140, useNativeDriver: Platform.OS !== 'web' });
      animation.start();
    }).catch(() => {});
    return () => { active = false; animation?.stop(); };
  }, [opacity]);
  return <Animated.View style={[styles.card, { opacity }]} testID="lesson-hint-panel">
    <View style={styles.header}><Ionicons name="bulb-outline" size={17} color={COLORS.primaryDark} accessible={false} />
      <Text style={styles.label}>GỢI Ý · CẤP {level}/{count}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Thu gọn gợi ý" onPress={onClose} style={styles.close}>
        <Text style={styles.link}>Thu gọn</Text><Ionicons name="chevron-up" size={15} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <MathText style={styles.body}>{text}</MathText>
    {level === count ? <Text style={styles.lastHint}>Em thử tự làm bước này nhé.</Text> : null}
    <View style={styles.actions}>
      <View style={styles.navigation}>
        {onPrevious ? <Pressable accessibilityRole="button" accessibilityLabel="Gợi ý trước" disabled={busy} onPress={onPrevious} style={styles.action}>
          <Ionicons name="chevron-back" size={14} color={COLORS.primaryDark} accessible={false} /><Text style={styles.link}>Trước</Text>
        </Pressable> : null}
        {onNext ? <Pressable accessibilityRole="button" accessibilityLabel="Gợi ý sau" disabled={busy} onPress={onNext} style={styles.action}>
          <Text style={styles.link}>Tiếp</Text><Ionicons name="chevron-forward" size={14} color={COLORS.primaryDark} accessible={false} />
        </Pressable> : null}
      </View>
      {onExplain ? <Pressable accessibilityRole="button" accessibilityLabel="Em muốn hiểu gợi ý rõ hơn" onPress={onExplain} style={styles.action}>
        <Text style={styles.link}>Giải thích cách làm</Text>
      </Pressable> : null}
    </View>
  </Animated.View>;
}

const styles = StyleSheet.create({
  card: { paddingHorizontal: 12, paddingTop: 1, borderRadius: 12, borderWidth: 1, borderColor: '#E1D6F6', backgroundColor: '#F5F0FE' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  label: { flex: 1, fontFamily: FONTS.extraBold, fontSize: 10, letterSpacing: .6, color: COLORS.primaryDark },
  close: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 3 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 21, color: COLORS.textPrimary },
  lastHint: { marginTop: 4, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 17, color: COLORS.textSecondary },
  actions: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', columnGap: 8 },
  navigation: { flexDirection: 'row', flexShrink: 1, flexWrap: 'wrap', columnGap: 8 },
  action: { minHeight: 44, minWidth: 44, flexDirection: 'row', alignItems: 'center', gap: 3 },
  link: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
});
