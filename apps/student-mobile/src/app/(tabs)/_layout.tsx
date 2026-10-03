import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';
import { View, StyleSheet, Pressable, Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
type StudentTabBarProps = Parameters<NonNullable<React.ComponentProps<typeof Tabs>['tabBar']>>[0];
const MENU = {
    index: { title: 'Trang chủ', icon: 'home-outline', active: 'home' },
    lessons: { title: 'Bài học', icon: 'book-outline', active: 'book' },
    achievements: { title: 'Thành tích', icon: 'trophy-outline', active: 'trophy' },
    profile: { title: 'Của em', icon: 'happy-outline', active: 'happy' },
} as const;

function StudentTabBar({ state, navigation }: StudentTabBarProps) {
    const insets = useSafeAreaInsets();
    if (state.routes[state.index]?.name === 'camera') return null;
    return <View accessibilityRole="tablist" style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 10) }]}>
      {state.routes.map((route, index) => {
        const item = MENU[route.name as keyof typeof MENU];
        if (!item) return null;
        const selected = state.index === index;
        return <Pressable key={route.key} accessibilityRole="tab" accessibilityLabel={item.title}
          accessibilityState={{ selected }} aria-selected={selected}
          onPress={() => {
            const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
            if (!selected && !event.defaultPrevented) navigation.navigate(route.name, route.params);
          }} onLongPress={() => navigation.emit({ type: 'tabLongPress', target: route.key })}
          style={({ pressed }) => [styles.item, selected && styles.selected, pressed && styles.pressed]}>
          <Ionicons name={selected ? item.active : item.icon} size={25}
            color={selected ? COLORS.primary : '#8C899B'} accessible={false} />
          <Text style={[styles.label, selected && styles.selectedLabel]}>{item.title}</Text>
        </Pressable>;
      })}
    </View>;
}
export default function TabLayout() {
    return (<Tabs screenOptions={{ headerShown: false }} tabBar={props => <StudentTabBar {...props} />}>
      <Tabs.Screen name="index" options={{ title: 'Trang chủ' }}/>
      <Tabs.Screen name="lessons" options={{ title: 'Bài học' }}/>
      <Tabs.Screen name="achievements" options={{ title: 'Thành tích' }}/>
      <Tabs.Screen name="profile" options={{ title: 'Của em' }}/>
      <Tabs.Screen name="camera" options={{ href: null }}/>
    </Tabs>);
}
const styles = StyleSheet.create({
    bar: { position: 'absolute', left: 0, right: 0, bottom: 0, flexDirection: 'row', paddingTop: 9,
        paddingHorizontal: 12, gap: 5, backgroundColor: '#FFFFFF', borderTopLeftRadius: 28,
        borderTopRightRadius: 28, shadowColor: '#7770B1', shadowOffset: { width: 0, height: -3 },
        shadowOpacity: 0.06, shadowRadius: 16, elevation: 8 },
    item: { flex: 1, minHeight: 59, justifyContent: 'center', alignItems: 'center', gap: 4,
        borderRadius: 20, paddingVertical: 7, paddingHorizontal: 2 },
    selected: { backgroundColor: '#F0EBFE' },
    label: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textMuted, textAlign: 'center' },
    selectedLabel: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
    pressed: { opacity: 0.65 },
});
