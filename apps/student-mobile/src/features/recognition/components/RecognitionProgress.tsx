import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, Image, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS } from '../../../constants/theme';

type Props = { title: string; description: string; imageUri?: string; onCancel?: () => void; cancelLabel?: string };

// The service does not report a completion percentage. This bar indicates work,
// never invents a percentage or promises an estimated finishing time.
export function RecognitionProgress({ title, description, imageUri, onCancel, cancelLabel = 'Quay lại' }: Props) {
  const motion = useRef(new Animated.Value(0)).current;
  const [width, setWidth] = useState(240);
  const [reduceMotion, setReduceMotion] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let active = true;
    AccessibilityInfo.isReduceMotionEnabled().then(value => { if (active) setReduceMotion(value); }).catch(() => {});
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => { active = false; subscription.remove(); clearInterval(timer); };
  }, []);

  useEffect(() => {
    motion.setValue(0);
    if (reduceMotion) return;
    const animation = Animated.loop(Animated.timing(motion, {
      toValue: 1, duration: 1500, easing: Easing.inOut(Easing.ease), useNativeDriver: Platform.OS !== 'web',
    }));
    animation.start();
    return () => animation.stop();
  }, [motion, reduceMotion]);

  return <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} nestedScrollEnabled>
    <View style={[styles.card, SHADOWS.small]}>
    {imageUri ? <Image source={{ uri: imageUri }} style={styles.image} resizeMode="contain" accessible={false} />
      : <View style={styles.icon}><Ionicons name="document-text-outline" size={32} color={COLORS.primary} accessible={false} /></View>}
    <Text style={styles.title} accessibilityRole="header">{title}</Text>
    <Text style={styles.description}>{description}</Text>
    <View style={styles.track} onLayout={event => setWidth(event.nativeEvent.layout.width)}
      accessibilityRole="progressbar" accessibilityLabel={title} accessibilityState={{ busy: true }}>
      <Animated.View style={[styles.bar, { width: width * 0.32,
        transform: [{ translateX: reduceMotion ? width * 0.34 : motion.interpolate({ inputRange: [0, 1], outputRange: [-width * 0.32, width] }) }],
      }]} />
    </View>
    <Text style={styles.time}>Đã chờ {elapsed} giây</Text>
    <Text style={styles.hint} accessibilityLiveRegion="polite">{elapsed >= 25
      ? 'Ảnh nhiều dòng có thể cần thêm thời gian. Em có thể quay lại mà vẫn giữ ảnh đã chọn.'
      : 'Ảnh của em vẫn được giữ trong khi xử lý.'}</Text>
    {onCancel ? <Pressable onPress={onCancel} accessibilityRole="button" accessibilityLabel={cancelLabel} style={({ pressed }) => [styles.cancel, pressed && { opacity: 0.65 }]}>
      <Ionicons name="arrow-back" size={18} color={COLORS.primaryDark} accessible={false} />
      <Text style={styles.cancelText}>{cancelLabel}</Text>
    </Pressable> : null}
    </View>
  </ScrollView>;
}

const styles = StyleSheet.create({
  scroll: { width: '100%', maxWidth: 440, maxHeight: '100%', flexGrow: 0, flexShrink: 1, alignSelf: 'center' },
  scrollContent: { paddingVertical: 6 },
  card: { width: '100%', maxWidth: 440, alignSelf: 'center', backgroundColor: COLORS.surface, borderRadius: 28, padding: 24, alignItems: 'center', borderWidth: 1, borderColor: COLORS.border },
  image: { width: '100%', height: 160, borderRadius: 18, backgroundColor: COLORS.surfaceSubdued, marginBottom: 24 },
  icon: { width: 72, height: 72, borderRadius: 24, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center', marginBottom: 24 },
  title: { fontSize: 22, fontWeight: '800', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 12 },
  description: { fontSize: 15, lineHeight: 23, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 24 },
  track: { width: '100%', height: 10, borderRadius: 5, overflow: 'hidden', backgroundColor: COLORS.primaryLight },
  bar: { height: 10, borderRadius: 5, backgroundColor: COLORS.primary },
  time: { fontSize: 13, color: COLORS.textMuted, marginTop: 12 },
  hint: { fontSize: 13, lineHeight: 20, color: COLORS.textSecondary, textAlign: 'center', marginTop: 12 },
  cancel: { minHeight: 48, flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20, marginTop: 16 },
  cancelText: { fontSize: 15, fontWeight: '700', color: COLORS.primaryDark },
});
