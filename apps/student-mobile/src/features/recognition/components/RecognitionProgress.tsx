import React, { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, Image, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS, SHADOWS } from '../../../constants/theme';

type Props = { title: string; description: string; imageUri?: string; onCancel?: () => void; cancelLabel?: string };
const MASCOT = require('../../../../assets/illustrations/mathvision-star.png');

// This service reports stages, not a completion percentage. Animate activity only.
export function RecognitionProgress({ title, description, imageUri, onCancel, cancelLabel = 'Quay lại' }: Props) {
  const [motion] = useState(() => new Animated.Value(0));
  const [width, setWidth] = useState(240);
  const [reduceMotion, setReduceMotion] = useState(true);
  const { height } = useWindowDimensions();
  const compact = height < 500;

  useEffect(() => {
    let active = true;
    AccessibilityInfo.isReduceMotionEnabled().then(value => { if (active) setReduceMotion(value); }).catch(() => {});
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    return () => { active = false; subscription.remove(); };
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

  return <ScrollView style={styles.scroll} contentContainerStyle={styles.content} nestedScrollEnabled showsVerticalScrollIndicator={false}>
    <LinearGradient colors={['#F2EEFF', '#E6DEFF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.scene, compact && styles.sceneCompact]}>
      <View style={styles.softCircle} />
      <View style={styles.littleCircle} />
      {imageUri ? <View style={[styles.paper, SHADOWS.small]}>
        <Image source={{ uri: imageUri }} style={styles.photo} resizeMode="contain" accessible={false} />
      </View> : null}
      <Image source={MASCOT} style={[imageUri ? styles.mascot : styles.mascotAlone, compact && styles.mascotCompact]}
        resizeMode="contain" accessible={false} />
      <View style={styles.sparkle}><Ionicons name="sparkles" size={18} color="#E5A930" accessible={false} /></View>
    </LinearGradient>

    <Text style={styles.title} accessibilityRole="header">{title}</Text>
    <Text style={styles.description}>{description}</Text>
    <View style={styles.track} onLayout={event => setWidth(event.nativeEvent.layout.width)}
      accessibilityRole="progressbar" accessibilityLabel={title} accessibilityState={{ busy: true }} aria-busy={true}>
      <Animated.View style={[styles.bar, { width: width * 0.34,
        transform: [{ translateX: reduceMotion ? width * 0.33 : motion.interpolate({ inputRange: [0, 1], outputRange: [-width * 0.34, width] }) }],
      }]}>
        <LinearGradient colors={['#B39AFF', '#7754F4']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.barFill} />
      </Animated.View>
    </View>
    {onCancel ? <>
      <Text style={styles.hint}>Ảnh của em vẫn được giữ.</Text>
      <Pressable onPress={onCancel} accessibilityRole="button" accessibilityLabel={cancelLabel}
        style={({ pressed }) => [styles.cancel, pressed && styles.pressed]}>
        <Ionicons name="arrow-back" size={17} color={COLORS.primaryDark} accessible={false} />
        <Text style={styles.cancelText}>{cancelLabel}</Text>
      </Pressable>
    </> : null}
  </ScrollView>;
}

const styles = StyleSheet.create({
  scroll: { width: '100%', maxWidth: 420, maxHeight: '100%', flexGrow: 0, flexShrink: 1, alignSelf: 'center' },
  content: { alignItems: 'center', paddingVertical: 8, paddingHorizontal: 2 },
  scene: { width: '100%', height: 206, borderRadius: 28, overflow: 'hidden', marginBottom: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EEE7FF' },
  sceneCompact: { height: 140, marginBottom: 16 },
  softCircle: { position: 'absolute', width: 190, height: 190, right: -64, top: -72, borderRadius: 95, backgroundColor: '#DFD3FF' },
  littleCircle: { position: 'absolute', width: 56, height: 56, left: 14, bottom: -28, borderRadius: 28, backgroundColor: '#D9EEE0' },
  paper: { position: 'absolute', left: 18, top: 15, bottom: 15, width: '74%', borderRadius: 17, padding: 8, backgroundColor: '#FFFFFF', transform: [{ rotate: '-3deg' }] },
  photo: { width: '100%', height: '100%', borderRadius: 10 },
  mascot: { position: 'absolute', right: -2, bottom: -5, width: 130, height: 150 },
  mascotAlone: { width: 180, height: 180 },
  mascotCompact: { width: 100, height: 120 },
  sparkle: { position: 'absolute', right: 21, top: 17 },
  title: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 31, color: COLORS.textPrimary, textAlign: 'center', marginBottom: 9 },
  description: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 22, color: COLORS.textSecondary, textAlign: 'center', marginBottom: 22, maxWidth: 330 },
  track: { width: '100%', height: 12, borderRadius: 6, overflow: 'hidden', backgroundColor: '#E9E3FC' },
  bar: { height: 12, borderRadius: 6, overflow: 'hidden', backgroundColor: COLORS.primary },
  barFill: { flex: 1 },
  hint: { fontFamily: FONTS.medium, fontSize: 12, lineHeight: 18, color: COLORS.textMuted, marginTop: 14 },
  cancel: { minHeight: 48, flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 22, marginTop: 14, borderRadius: 24, backgroundColor: '#ECE5FF' },
  cancelText: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  pressed: { opacity: 0.65 },
});
