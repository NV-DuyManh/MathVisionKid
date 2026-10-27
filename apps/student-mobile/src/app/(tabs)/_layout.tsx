import React, { useRef, useState } from 'react';
import { Tabs, Redirect } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, View, StyleSheet, Pressable, Text, ScrollView, Platform, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, FONTS } from '../../constants/theme';
import { StudentNavIcon } from '../../components/ui/StudentNavIcon';
import { LinearGradient } from 'expo-linear-gradient';
import { AppIllustration } from '../../components/ui/AppIllustration';
import type { KeyDownEvent, PressableStateCallbackType, ViewInstance } from 'react-native';

type StudentTabBarProps = Parameters<NonNullable<React.ComponentProps<typeof Tabs>['tabBar']>>[0];
const MENU = { index: 'Trang chủ', lessons: 'Bài học', achievements: 'Thành tích', profile: 'Của em' } as const;

export function StudentTabBar({ state, emitter, navigateToTab, viewportWidth, expanded: controlled, onToggle }: StudentTabBarProps & {
  viewportWidth?: number; expanded?: boolean; onToggle?: () => void;
}) {
  const insets = useSafeAreaInsets();
  const dimensions = useWindowDimensions();
  const width = viewportWidth ?? dimensions.width;
  const wide = width >= 768;
  const [preference, setPreference] = useState<boolean | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const refs = useRef(new Map<string, ViewInstance>());
  const expanded = controlled ?? preference ?? width >= 1200;

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
        {...(Platform.OS === 'web' ? { tabIndex: selected ? 0 : -1, title: wide && !expanded ? title : undefined, onKeyDown: (event: React.KeyboardEvent | KeyDownEvent) => {
          const key = 'key' in event ? event.key : event.nativeEvent.key;
          const routes = state.routes.filter(item => item.name in MENU);
          const current = routes.findIndex(item => item.key === route.key);
          const next = wide ? 'ArrowDown' : 'ArrowRight';
          const previous = wide ? 'ArrowUp' : 'ArrowLeft';
          let target = current;
          if (key === next) target = (current + 1) % routes.length;
          else if (key === previous) target = (current + routes.length - 1) % routes.length;
          else if (key === 'Home') target = 0;
          else if (key === 'End') target = routes.length - 1;
          else return;
          event.preventDefault();
          refs.current.get(routes[target].key)?.focus();
        } } : {})}
        onPress={() => {
          const event = emitter.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
          if (!selected && !event.defaultPrevented) navigateToTab(route.key);
        }} onLongPress={() => emitter.emit({ type: 'tabLongPress', target: route.key })}
        style={({ pressed, hovered }: PressableStateCallbackType & { hovered?: boolean }) => [styles.item, wide && styles.sideItem,
          wide && !expanded && styles.compactItem, selected && styles.selected, wide && selected && styles.sideSelected,
          hovered && (wide ? styles.sideHovered : styles.hovered), focused === route.key && styles.focused, pressed && styles.pressed]}>
        {wide ? <Ionicons name={({ index: 'home-outline', lessons: 'book-outline', achievements: 'medal-outline', profile: 'person-outline' } as const)[name]} size={24} color="#FFFFFF" accessible={false} /> : <StudentNavIcon name={name} size={30} />}
        {(!wide || expanded) && <Text style={[styles.label, selected && styles.selectedLabel, wide && styles.sideLabel]}>{title}</Text>}
      </Pressable>;
    })}
  </View>;

  if (!wide) return <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 10) }]}>{destinations}</View>;
  return <LinearGradient colors={['#352A7D', '#2B1D6C', '#352479']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.sidebar, { width: expanded ? 248 : 80, paddingTop: Math.max(insets.top, 25), paddingBottom: Math.max(insets.bottom, 20) }]}>
    <View style={[styles.brand, !expanded && styles.compactBrand]}>
      <AppIllustration source={require('../../../assets/images/mathvision-icon-v2.png')} style={{ width: 31, height: 31, borderRadius: 16 }} accessible={false} />
      {expanded && <Text style={styles.brandText}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>}
    </View>
    <Pressable accessibilityRole="button" accessibilityLabel={expanded ? 'Thu gọn menu' : 'Mở rộng menu'}
      accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls="student-destinations"
      onFocus={() => setFocused('toggle')} onBlur={() => setFocused(null)}
      onPress={onToggle || (() => setPreference(!expanded))}
      style={({ pressed, hovered }: PressableStateCallbackType & { hovered?: boolean }) => [styles.toggle, hovered && styles.hovered, focused === 'toggle' && styles.focused, pressed && styles.pressed]}>
      <Ionicons name={expanded ? 'chevron-back' : 'chevron-forward'} size={19} color="#DCD0FF" accessible={false} />
      {expanded && <Text style={styles.toggleText}>Thu gọn</Text>}
    </Pressable>
    <ScrollView nativeID="student-destinations" showsVerticalScrollIndicator={false} contentContainerStyle={styles.sidebarScroll}>{destinations}</ScrollView>
    {expanded && <View style={styles.sidebarNote}><AppIllustration source={require('../../../assets/illustrations/mathvision-star.png')} style={styles.sidebarMascot} accessible={false} /><Text style={styles.noteTitle}>Một chút mỗi ngày</Text><Text style={styles.noteText}>Cùng em hiểu bài, tự tin hơn.</Text></View>}
  </LinearGradient>;
}

export default function TabLayout() {
  const { width } = useWindowDimensions();
  const [preference, setPreference] = useState<boolean | null>(null);
  const expanded = preference ?? width >= 1200;
  const auth = React.useContext(AuthContext);
  if (auth?.isLoading) return <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}><ActivityIndicator accessibilityLabel="Đang xác minh tài khoản" /></View>;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || auth.user?.active !== true) return <Redirect href="/login" />;
  return <Tabs screenOptions={{ headerShown: false, tabBarPosition: width >= 768 ? 'left' : 'bottom' }}
    tabBar={props => <StudentTabBar {...props} viewportWidth={width} expanded={expanded} onToggle={() => setPreference(!expanded)} />}>
    <Tabs.Screen name="index" options={{ title: 'Trang chủ' }} />
    <Tabs.Screen name="lessons" options={{ title: 'Bài học' }} />
    <Tabs.Screen name="achievements" options={{ title: 'Thành tích' }} />
    <Tabs.Screen name="profile" options={{ title: 'Của em' }} />
  </Tabs>;
}

const styles = StyleSheet.create({
  bar: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingTop: 8, paddingHorizontal: 12,
    backgroundColor: '#FFFFFF', borderTopLeftRadius: 26, borderTopRightRadius: 26,
    shadowColor: '#7770B1', shadowOffset: { width: 0, height: -3 }, shadowOpacity: .07, shadowRadius: 16, elevation: 8 },
  items: { flexDirection: 'row', gap: 6 }, vertical: { flexDirection: 'column', gap: 9 },
  item: { flex: 1, minHeight: 62, justifyContent: 'center', alignItems: 'center', gap: 3, borderRadius: 18, paddingVertical: 6, paddingHorizontal: 2 },
  selected: { backgroundColor: '#F0EAFF' },
  label: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#625978', textAlign: 'center' },
  selectedLabel: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  sidebar: { flexShrink: 0, borderRightWidth: 1, borderRightColor: '#4C398E', paddingHorizontal: 15 },
  sidebarScroll: { paddingTop: 18, paddingBottom: 90 },
  sideItem: { flex: 0, flexDirection: 'row', justifyContent: 'flex-start', minHeight: 60, paddingHorizontal: 15, gap: 13, borderRadius: 16 },
  sideSelected: { backgroundColor: '#7850F4', borderWidth: 1, borderColor: '#A582FF', shadowColor: '#170B4C', shadowOpacity: .2, shadowRadius: 7, shadowOffset: { width: 0, height: 3 } },
  sideHovered: { backgroundColor: '#6747B6' },
  compactItem: { justifyContent: 'center', paddingHorizontal: 4 },
  sideLabel: { fontSize: 16, textAlign: 'left', flexShrink: 1, color: '#FFFFFF' },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 5, minHeight: 48, paddingHorizontal: 1, marginBottom: 8 },
  compactBrand: { justifyContent: 'center' },
  brandText: { fontFamily: FONTS.black, fontSize: 18, letterSpacing: -.7, color: '#FFFFFF', flexShrink: 1 },
  brandAccent: { color: '#DED2FF' },
  toggle: { minHeight: 44, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9, backgroundColor: '#FFFFFF0A', borderRadius: 13 },
  toggleText: { fontFamily: FONTS.bold, fontSize: 12, color: '#DCD0FF' },
  sidebarNote: { backgroundColor: '#7555BB40', borderRadius: 19, padding: 18, paddingTop: 50, gap: 7, marginTop: 52 },
  sidebarMascot: { width: 116, height: 116, position: 'absolute', left: 48, top: -73 },
  noteTitle: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#FFF' },
  noteText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: '#D9CDED' },
  hovered: { backgroundColor: '#F4F0FF' }, focused: { outlineColor: '#6845DB', outlineWidth: 2, outlineOffset: 2 },
  pressed: { opacity: .72 },
});
