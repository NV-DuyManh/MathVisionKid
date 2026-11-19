import React, { type ComponentProps, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';

type Icon = ComponentProps<typeof Ionicons>['name'];
type Tone = 'purple' | 'yellow' | 'green' | 'blue';

const tones: Record<Tone, { tint: string; ink: string }> = {
  purple: { tint: '#EEE7FF', ink: '#5732B3' },
  yellow: { tint: '#FFF1CB', ink: '#825120' },
  green: { tint: '#DEF6EB', ink: '#146448' },
  blue: { tint: '#E4EFFF', ink: '#34589F' },
};

export type PersonalMetric = { label: string; amount?: number; icon: Icon; tone: Tone };

export function PersonalPageHeader({ title, backLabel, onBack, onAccount, keepOnDesktop = false }: {
  title: string; backLabel: string; onBack: () => void; onAccount?: () => void; keepOnDesktop?: boolean;
}) {
  return <View style={styles.pageHeader} {...(!keepOnDesktop ? { dataSet: { studentSecondaryHeader: 'true' } } : {})}>
    <Pressable accessibilityRole="button" accessibilityLabel={backLabel} onPress={onBack}
      style={({ pressed }) => [styles.headerButton, pressed && styles.pressed]}>
      <Ionicons name="chevron-back" size={22} color={STUDENT_WEB.primary} accessible={false} />
    </Pressable>
    <Text accessibilityRole="header" aria-level={1} style={styles.pageTitle}>{title}</Text>
    {onAccount && <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={onAccount}
      style={({ pressed }) => [styles.headerButton, pressed && styles.pressed]}>
      <Ionicons name="person-outline" size={22} color={STUDENT_WEB.primary} accessible={false} />
    </Pressable>}
  </View>;
}

export function PersonalMetrics({ metrics }: { metrics: PersonalMetric[] }) {
  return <View style={styles.metrics}>{metrics.map(({ label, amount, icon, tone }) =>
    <View key={label} style={styles.metric}>
      <PersonalIcon icon={icon} tone={tone} />
      <View style={styles.grow}>
        <Text style={styles.metricValue}>{amount === undefined ? '—' : amount.toLocaleString('vi-VN')}</Text>
        <Text style={styles.body}>{label}</Text>
      </View>
    </View>)}</View>;
}

export function PersonalPanel({ title, icon, children }: { title: string; icon?: Icon; children: ReactNode }) {
  return <View style={styles.panel}>
    <View style={styles.panelHeading}>
      {icon && <Ionicons name={icon} size={22} color={STUDENT_WEB.primary} accessible={false} />}
      <Text accessibilityRole="header" aria-level={2} style={styles.heading}>{title}</Text>
    </View>
    {children}
  </View>;
}

export function PersonalLink({ label, description, icon, tone, onPress, accessibilityLabel }: {
  label: string; description?: string; icon: Icon; tone: Tone; onPress: () => void; accessibilityLabel?: string;
}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={accessibilityLabel ?? label} onPress={onPress}
    style={({ pressed }) => [styles.link, { backgroundColor: tones[tone].tint }, pressed && styles.pressed]}>
    <PersonalIcon icon={icon} tone={tone} />
    <View style={styles.grow}><Text style={styles.linkLabel}>{label}</Text>{description && <Text style={styles.body}>{description}</Text>}</View>
    <Ionicons name="chevron-forward" size={18} color={tones[tone].ink} accessible={false} />
  </Pressable>;
}

function PersonalIcon({ icon, tone }: { icon: Icon; tone: Tone }) {
  return <View style={[styles.icon, { backgroundColor: tones[tone].tint }]}><Ionicons name={icon} size={22} color={tones[tone].ink} accessible={false} /></View>;
}

export const personalWebStyles = StyleSheet.create({
  panel: { backgroundColor: STUDENT_WEB.surface, borderRadius: 17, borderColor: STUDENT_WEB.border, borderWidth: 1, padding: 15, gap: 11, boxShadow: '0 5px 15px #49348308' },
  heading: { fontFamily: FONTS.extraBold, fontSize: 20, lineHeight: 28, color: STUDENT_WEB.ink },
  body: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 20, color: STUDENT_WEB.muted },
  columns: { gap: 18 },
  wide: { flexDirection: 'row', alignItems: 'flex-start' },
  stack: { gap: 18, minWidth: 0 },
  mainGrow: { flex: 2 },
  sideGrow: { flex: 1 },
});

const styles = StyleSheet.create({
  ...personalWebStyles,
  panelHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  pageHeader: { minHeight: 54, flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerButton: { width: 44, height: 44, borderRadius: 13, justifyContent: 'center', alignItems: 'center',
    borderWidth: 1, borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.surface },
  pageTitle: { flex: 1, minWidth: 0, fontFamily: FONTS.black, fontSize: 25, lineHeight: 32, color: STUDENT_WEB.ink },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  metric: { flexGrow: 1, flexBasis: 150, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 13,
    backgroundColor: STUDENT_WEB.surface, borderRadius: 17, borderWidth: 1, borderColor: STUDENT_WEB.border },
  metricValue: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 29, color: STUDENT_WEB.ink },
  icon: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 13, flexShrink: 0 },
  grow: { flex: 1, minWidth: 0 },
  link: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 14, padding: 8 },
  linkLabel: { fontFamily: FONTS.extraBold, fontSize: 15, lineHeight: 21, color: STUDENT_WEB.ink },
  pressed: { opacity: .75 },
});
