import React from 'react';
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';

export function LessonSheet({ title, onClose, children, footer, compact = false }: {
  title: string; onClose: () => void; children: React.ReactNode; footer?: React.ReactNode; compact?: boolean;
}) {
  const { width, height } = useWindowDimensions();
  const short=height<500;
  const horizontalPadding = width < 360 ? 16 : 24;
  return <Modal visible animationType="none" transparent accessibilityLabel={title} onRequestClose={onClose}>
    <SafeAreaView style={styles.scrim}><KeyboardAvoidingView style={styles.shell} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><View style={[styles.sheet, !compact && { minHeight: Math.min(height * .6, 480) }]} accessibilityViewIsModal>
      <View style={[styles.header,short&&{paddingVertical:7}]}><Text accessibilityRole="header" style={[styles.title,short&&{fontSize:18}]}>{title}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={`Đóng ${title}`} onPress={onClose} style={styles.close}>
          <Ionicons name="close" size={24} color={COLORS.textPrimary} /></Pressable></View>
      <ScrollView style={compact && styles.compactScroll} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" contentContainerStyle={[styles.content, { paddingHorizontal: horizontalPadding },short&&{paddingVertical:12}]}>{children}</ScrollView>
      {footer && <View style={[styles.footer, { paddingHorizontal: horizontalPadding }]}>{footer}</View>}
    </View></KeyboardAvoidingView></SafeAreaView>
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
});
