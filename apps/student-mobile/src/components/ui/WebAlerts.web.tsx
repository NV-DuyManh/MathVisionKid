import React, { useEffect, useState } from 'react';
import { Alert, AlertButton, AlertOptions, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';

type Dialog = { title: string; message?: string; buttons: AlertButton[]; options?: AlertOptions };

/** React Native Web leaves Alert.alert empty; keep the app's existing confirmations working. */
export function WebAlerts() {
  const [dialog, setDialog] = useState<Dialog | null>(null);
  useEffect(() => {
    const original = Alert.alert;
    const show: typeof Alert.alert = (title, message, buttons, options) => {
      setDialog({ title, message, buttons: buttons?.length ? buttons : [{ text: 'Đã hiểu' }], options });
    };
    Alert.alert = show;
    return () => { if (Alert.alert === show) Alert.alert = original; };
  }, []);

  if (!dialog) return null;
  const dismiss = () => {
    if (dialog.options?.cancelable === false) return;
    setDialog(null);
    dialog.options?.onDismiss?.();
  };
  return <Modal visible transparent animationType="fade" accessibilityLabel={dialog.title} onRequestClose={dismiss}>
    <View style={styles.backdrop}>
      <View style={styles.card}>
        <ScrollView style={styles.content}>
          <Text accessibilityRole="header" style={styles.title}>{dialog.title}</Text>
          {dialog.message ? <Text style={styles.message}>{dialog.message}</Text> : null}
        </ScrollView>
        <View style={styles.actions}>
          {dialog.buttons.map((button, index) => <Pressable key={index} accessibilityRole="button"
            accessibilityLabel={button.text || 'Đã hiểu'}
            onPress={() => { setDialog(null); button.onPress?.(); }}
            style={({ pressed }) => [styles.button, button.style === 'cancel' && styles.cancel,
              button.style === 'destructive' && styles.destructive, pressed && styles.pressed]}>
            <Text style={[styles.buttonText, button.style === 'cancel' && styles.cancelText]}>{button.text || 'Đã hiểu'}</Text>
          </Pressable>)}
        </View>
      </View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(24, 22, 76, .5)', alignItems: 'center', justifyContent: 'center', padding: 20 },
  card: { width: '100%', maxWidth: 440, maxHeight: '90%', backgroundColor: COLORS.surface, borderRadius: 26, padding: 24, gap: 22 },
  content: { flexShrink: 1 },
  title: { fontFamily: FONTS.extraBold, fontSize: 22, color: COLORS.textPrimary },
  message: { fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, color: COLORS.textSecondary, marginTop: 12 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  button: { flexGrow: 1, minWidth: 100, minHeight: 48, alignItems: 'center', justifyContent: 'center', padding: 12, backgroundColor: COLORS.primary, borderRadius: 20 },
  cancel: { backgroundColor: COLORS.surfaceSubdued }, destructive: { backgroundColor: COLORS.error },
  buttonText: { fontFamily: FONTS.bold, fontSize: 16, color: COLORS.surface }, cancelText: { color: COLORS.primaryDark },
  pressed: { opacity: .75 },
});
