import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';

type Action = { label: string; onPress: () => void; accessibilityLabel?: string; disabled?: boolean; icon?: React.ComponentProps<typeof Ionicons>['name'] };

/** A short explanation and recovery actions; the current work stays on screen. */
export function RecoveryNotice({ title, message, actions = [], messageId }: {
  title: string; message?: string; actions?: Action[]; messageId?: string;
}) {
  const [focused, setFocused] = useState<number | null>(null);
  return <View testID="recovery-notice" style={styles.card}>
    <View nativeID={messageId} accessibilityRole="alert" accessibilityLiveRegion="polite" style={styles.heading}>
      <View style={styles.badge} accessible={false}><Ionicons name="alert-circle-outline" size={18} color="#8E6A3C" accessible={false} /></View>
      <View style={styles.words}><Text style={styles.title}>{title}</Text>{message ? <Text style={styles.message}>{message}</Text> : null}</View>
    </View>
    {actions.length ? <View style={styles.actions}>{actions.map((action, index) => <Pressable key={action.accessibilityLabel || action.label}
      accessibilityRole="button" accessibilityLabel={action.accessibilityLabel || action.label} disabled={action.disabled}
      accessibilityState={{ disabled: !!action.disabled }} onPress={action.onPress}
      onFocus={() => setFocused(index)} onBlur={() => setFocused(null)}
      style={({ pressed }) => [styles.button, index === 0 && styles.primary, focused === index && styles.focused, (pressed || action.disabled) && styles.dimmed]}>
      {action.icon ? <Ionicons name={action.icon} size={16} color={index === 0 ? '#FFFFFF' : '#65458F'} accessible={false} /> : null}
      <Text style={[styles.label, index === 0 && styles.primaryLabel]}>{action.label}</Text>
    </Pressable>)}</View> : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 12, gap: 12, borderRadius: 17, borderWidth: 1, borderColor: '#E6DDEF', backgroundColor: '#FCFAFF' },
  heading: { flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  badge: { width: 28, height: 28, borderRadius: 9, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FAF0DE' },
  words: { flex: 1, minWidth: 0, gap: 3 },
  title: { fontFamily: FONTS.bold, fontSize: 14, lineHeight: 20, color: COLORS.textPrimary },
  message: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: '#6F627F' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  button: { flexGrow: 1, flexBasis: 100, minWidth: 0, minHeight: 44, paddingHorizontal: 10, paddingVertical: 9, borderRadius: 12,
    borderWidth: 1.5, borderColor: '#DDD2EE', backgroundColor: '#FFFFFF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  primary: { borderColor: '#7650D3', backgroundColor: '#7650D3' },
  focused: { borderColor: COLORS.textPrimary, outlineColor: COLORS.textPrimary, outlineStyle: 'solid', outlineWidth: 2, outlineOffset: 2 },
  label: { flexShrink: 1, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 18, color: '#65458F', textAlign: 'center' },
  primaryLabel: { color: '#FFFFFF' }, dimmed: { opacity: .65 },
});
