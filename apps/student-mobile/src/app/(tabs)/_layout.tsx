import React, { useRef, useState } from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, StyleSheet, Pressable, Text, ScrollView, Platform, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, FONTS } from '../../constants/theme';
import { StudentNavIcon } from '../../components/ui/StudentNavIcon';

type StudentTabBarProps = Parameters<NonNullable<React.ComponentProps<typeof Tabs>['tabBar']>>[0];
const MENU = { index: 'Trang chủ', lessons: 'Bài học', achievements: 'Thành tích', profile: 'Của em' } as const;

export function StudentTabBar({ state, navigation, viewportWidth, expanded: controlled, onToggle }: StudentTabBarProps & {
  viewportWidth?: number; expanded?: boolean; onToggle?: () => void;
}) {
  const insets = useSafeAreaInsets();
  const dimensions = useWindowDimensions();
  const width = viewportWidth ?? dimensions.width;
  const wide = width >= 768;
  const [preference, setPreference] = useState<boolean | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const refs = useRef(new Map<string, View>());
  const expanded = controlled ?? preference ?? width >= 1200;
  if (state.routes[state.index]?.name === 'camera') return null;

  const destinations = <View accessibilityRole="tablist" aria-orientation={wide ? 'vertical' : 'horizontal'}
    style={[styles.items, wide && styles.vertical]}>
    {state.routes.map((route, index) => {
      const name = route.name as keyof typeof MENU;
      const title = MENU[name];
      if (!title) return null;
      const selected = state.index === index;
      return <Pressable key={route.key} accessibilityRole="tab" accessibilityLabel={title}
        accessibilityState={{ selected }} aria-selected={selected}
        ref={node => { if (node) refs.current.set(route.key, node); else refs.current.delete(route.key); }}
        onFocus={() => setFocused(route.key)} onBlur={() => setFocused(null)}
        {...(Platform.OS === 'web' ? { tabIndex: selected ? 0 : -1, title: wide && !expanded ? title : undefined, onKeyDown: (event: React.KeyboardEvent) => {
          const routes = state.routes.filter(item => item.name in MENU);
          const current = routes.findIndex(item => item.key === route.key);
          const next = wide ? 'ArrowDown' : 'ArrowRight';
          const previous = wide ? 'ArrowUp' : 'ArrowLeft';
          let target = current;
          if (event.key === next) target = (current + 1) % routes.length;
          else if (event.key === previous) target = (current + routes.length - 1) % routes.length;
          else if (event.key === 'Home') target = 0;
          else if (event.key === 'End') target = routes.length - 1;
          else return;
          event.preventDefault();
          refs.current.get(routes[target].key)?.focus();
        } } : {})}
        onPress={() => {
          const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
          if (!selected && !event.defaultPrevented) navigation.navigate(route.name, route.params);
        }} onLongPress={() => navigation.emit({ type: 'tabLongPress', target: route.key })}
        style={({ pressed, hovered }) => [styles.item, wide && styles.sideItem,
          wide && !expanded && styles.compactItem, selected && styles.selected,
          hovered && styles.hovered, focused === route.key && styles.focused, pressed && styles.pressed]}>
        <StudentNavIcon name={name} size={wide ? 34 : 29} />
        {(!wide || expanded) && <Text style={[styles.label, wide && styles.sideLabel, selected && styles.selectedLabel]}>{title}</Text>}
      </Pressable>;
    })}
  </View>;

  if (!wide) return <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 10) }]}>{destinations}</View>;
  return <View style={[styles.sidebar, { width: expanded ? 216 : 80, paddingTop: Math.max(insets.top, 20), paddingBottom: Math.max(insets.bottom, 16) }]}>
    <View style={[styles.brand, !expanded && styles.compactBrand]}>
      <StudentNavIcon name="index" size={36} />
      {expanded && <Text style={styles.brandText}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>}
    </View>
    <Pressable accessibilityRole="button" accessibilityLabel={expanded ? 'Thu gọn menu' : 'Mở rộng menu'}
      accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls="student-destinations"
      onFocus={() => setFocused('toggle')} onBlur={() => setFocused(null)}
      onPress={onToggle || (() => setPreference(!expanded))}
      style={({ pressed, hovered }) => [styles.toggle, hovered && styles.hovered, focused === 'toggle' && styles.focused, pressed && styles.pressed]}>
      <Ionicons name={expanded ? 'chevron-back' : 'chevron-forward'} size={19} color={COLORS.primaryDark} accessible={false} />
      {expanded && <Text style={styles.toggleText}>Thu gọn</Text>}
    </Pressable>
    <ScrollView nativeID="student-destinations" showsVerticalScrollIndicator={false} contentContainerStyle={styles.sidebarScroll}>{destinations}</ScrollView>
    {expanded && <View style={styles.sidebarNote}><Text style={styles.noteTitle}>Một chút mỗi ngày</Text><Text style={styles.noteText}>Cùng em hiểu bài, tự tin hơn.</Text></View>}
  </View>;
}

export default function TabLayout() {
  const { width } = useWindowDimensions();
  const [preference, setPreference] = useState<boolean | null>(null);
  const expanded = preference ?? width >= 1200;
  return <Tabs screenOptions={{ headerShown: false, tabBarPosition: width >= 768 ? 'left' : 'bottom' }}
    tabBar={props => <StudentTabBar {...props} viewportWidth={width} expanded={expanded} onToggle={() => setPreference(!expanded)} />}>
    <Tabs.Screen name="index" options={{ title: 'Trang chủ' }} />
    <Tabs.Screen name="lessons" options={{ title: 'Bài học' }} />
    <Tabs.Screen name="achievements" options={{ title: 'Thành tích' }} />
    <Tabs.Screen name="profile" options={{ title: 'Của em' }} />
    <Tabs.Screen name="camera" options={{ href: null }} />
  </Tabs>;
}

const styles = StyleSheet.create({
  bar: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingTop: 8, paddingHorizontal: 12,
    backgroundColor: '#FFFFFF', borderTopLeftRadius: 26, borderTopRightRadius: 26,
    shadowColor: '#7770B1', shadowOffset: { width: 0, height: -3 }, shadowOpacity: .07, shadowRadius: 16, elevation: 8 },
  items: { flexDirection: 'row', gap: 6 }, vertical: { flexDirection: 'column', gap: 9 },
  item: { flex: 1, minHeight: 62, justifyContent: 'center', alignItems: 'center', gap: 3, borderRadius: 18, paddingVertical: 6, paddingHorizontal: 2 },
  selected: { backgroundColor: '#EEE8FF' },
  label: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#625978', textAlign: 'center' },
  selectedLabel: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  sidebar: { flexShrink: 0, borderRightWidth: 1, borderRightColor: '#EDE7FA', backgroundColor: '#FFFFFF', paddingHorizontal: 12 },
  sidebarScroll: { paddingTop: 16, paddingBottom: 16 },
  sideItem: { flex: 0, flexDirection: 'row', justifyContent: 'flex-start', minHeight: 58, paddingHorizontal: 12, gap: 12 },
  compactItem: { justifyContent: 'center', paddingHorizontal: 4 },
  sideLabel: { fontSize: 15, textAlign: 'left', flexShrink: 1 },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 5, minHeight: 48, paddingHorizontal: 1, marginBottom: 8 },
  compactBrand: { justifyContent: 'center' },
  brandText: { fontFamily: FONTS.black, fontSize: 17, letterSpacing: -.7, color: COLORS.textPrimary, flexShrink: 1 },
  brandAccent: { color: COLORS.primary },
  toggle: { minHeight: 48, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9, backgroundColor: '#F8F5FF', borderRadius: 15 },
  toggleText: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
  sidebarNote: { backgroundColor: '#F8F5FF', borderRadius: 18, padding: 14, gap: 5 },
  noteTitle: { fontFamily: FONTS.extraBold, fontSize: 13, color: COLORS.primaryDark },
  noteText: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: COLORS.textSecondary },
  hovered: { backgroundColor: '#F4F0FF' }, focused: { outlineColor: '#6845DB', outlineWidth: 2, outlineOffset: 2 },
  pressed: { opacity: .72 },
});
