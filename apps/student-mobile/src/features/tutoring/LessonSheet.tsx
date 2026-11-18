import React, { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Path } from 'react-native-svg';
import { COLORS, FONTS } from '../../constants/theme';

export function LessonSheet({ title, onClose, children, footer, compact = false, appearance }: {
  title: string; onClose: () => void; children: React.ReactNode; footer?: React.ReactNode; compact?: boolean; appearance?: 'hint';
}) {
  const { width, height } = useWindowDimensions();
  const hint = appearance === 'hint';
  const [opacity] = useState(() => new Animated.Value(1));
  useEffect(() => {
    if (!hint) return;
    let active = true;
    let reduced = false;
    void AccessibilityInfo.isReduceMotionEnabled().then(enabled => {
      if (!active || reduced || enabled) return;
      opacity.setValue(.86);
      Animated.timing(opacity, { toValue: 1, duration: 160, useNativeDriver: Platform.OS !== 'web' }).start();
    }, () => {});
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', enabled => {
      reduced = enabled;
      if (enabled) opacity.setValue(1);
    });
    return () => { active = false; subscription?.remove(); opacity.stopAnimation(); };
  }, [hint, opacity]);
  const short=height<500;
  const horizontalPadding = width < 360 ? (hint ? 12 : 16) : (hint ? 18 : 24);
  return <Modal visible animationType="none" transparent accessibilityLabel={title} onRequestClose={onClose}>
    <SafeAreaView style={[styles.scrim, hint && styles.hintScrim]}><KeyboardAvoidingView testID={hint ? 'hint-sheet-safe-viewport' : undefined}
      style={styles.shell} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Animated.View testID={hint ? 'hint-sheet-panel' : undefined}
        style={[styles.sheet, hint ? [styles.hintSheet, { opacity }] : !compact && { minHeight: Math.min(height * .6, 480) }]} accessibilityViewIsModal>
      <View style={[styles.header, hint && styles.hintHeader, short&&{paddingVertical:7}]}>
        {hint ? <>
          <LinearGradient colors={['#F7E5FF', '#E8E3FD', '#E9F0FF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill} pointerEvents="none" accessible={false} />
          <Svg width="100%" height="100%" viewBox="0 0 360 72" preserveAspectRatio="none" style={StyleSheet.absoluteFill}
            pointerEvents="none" accessible={false} aria-hidden>
            <Path d="M0 39C69 2 112 3 177 17S275 54 360 9V0H0Z" fill="#FFFFFF" opacity={.46} />
          </Svg>
          <View style={styles.hintIcon}><Ionicons name="bulb" size={22} color="#906000" accessible={false} aria-hidden /></View>
        </> : null}
        {hint ? <View style={styles.hintTitleWrap}>
          <Text accessibilityRole="header" style={[styles.title, styles.hintTitle, short && { fontSize: 18 }]}>{title}</Text>
          <View style={styles.hintAccent} aria-hidden />
        </View> : <Text accessibilityRole="header" style={[styles.title,short&&{fontSize:18}]}>{title}</Text>}
        <Pressable accessibilityRole="button" accessibilityLabel={`Đóng ${title}`} onPress={onClose}
          style={({ pressed }) => [styles.close, hint && styles.hintClose, hint && pressed && styles.pressed]}>
          <Ionicons name="close" size={24} color={hint ? COLORS.primaryDark : COLORS.textPrimary} accessible={false} /></Pressable></View>
      <ScrollView testID={hint ? 'hint-sheet-body' : undefined} style={hint ? styles.hintScroll : compact && styles.compactScroll}
        keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag"
        contentContainerStyle={[styles.content, hint && styles.hintContent, { paddingHorizontal: horizontalPadding },short&&{paddingVertical:12}]}>{children}</ScrollView>
      {footer && <View style={[styles.footer, { paddingHorizontal: horizontalPadding }]}>{footer}</View>}
    </Animated.View></KeyboardAvoidingView></SafeAreaView>
  </Modal>;
}
const styles = StyleSheet.create({
  scrim: { flex: 1, backgroundColor: '#21164788', alignItems: 'center', justifyContent: 'center', padding: 14 },
  shell: { flex: 1, width: '100%', maxWidth: 640, justifyContent: 'center' },
  sheet: { width: '100%', maxWidth: 640, maxHeight: '94%', borderRadius: 28, backgroundColor: '#FFFFFF', overflow: 'hidden', borderWidth: 1, borderColor: '#EAE2FA' },
  header: { padding: 16, paddingLeft: 22, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: '#EEE9F8' },
  title: { flex: 1, fontFamily: FONTS.bold, fontSize: 21, color: COLORS.textPrimary },
  close: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#F4F0FC', alignItems: 'center', justifyContent: 'center' },
  content: { flexGrow: 1, padding: 23, paddingBottom: 30, gap: 20 },
  compactScroll: { flexGrow: 0 },
  footer: { paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#EEE9F8', flexShrink: 0 },
  hintScrim: { padding: 8 },
  hintSheet: { flexShrink: 1, maxHeight: '100%', backgroundColor: '#FCFAFF', borderColor: '#DED0F5', borderRadius: 28 },
  hintScroll: { flexGrow: 0, flexShrink: 1 },
  hintHeader: { flexShrink: 0, padding: 12, paddingLeft: 16, gap: 8, borderBottomColor: '#E7DCF9' },
  hintTitleWrap: { flex: 1, minWidth: 0, gap: 3 },
  hintTitle: { flex: 0, fontFamily: FONTS.extraBold, color: COLORS.textPrimary },
  hintAccent: { width: 38, height: 3, borderRadius: 3, backgroundColor: '#EDBA3A' },
  hintIcon: { backgroundColor: '#FFF2CB', width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  hintClose: { backgroundColor: COLORS.surface },
  hintContent: { flexGrow: 0, paddingTop: 12, paddingBottom: 16, gap: 16 },
  pressed: { opacity: .7 },
});
