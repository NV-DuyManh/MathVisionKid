import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../constants/theme';
import { View, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
export default function TabLayout() {
    const insets = useSafeAreaInsets();
    return (<Tabs screenOptions={{
            headerShown: false,
            tabBarActiveTintColor: COLORS.primary,
            tabBarInactiveTintColor: COLORS.textSecondary,
            tabBarStyle: {
                backgroundColor: COLORS.surface,
                borderTopColor: COLORS.primaryLight,
                borderTopWidth: 1,
                height: 68 + Math.max(insets.bottom, 8),
                paddingTop: 8,
                paddingBottom: Math.max(insets.bottom, 8),
                borderTopLeftRadius: 24,
                borderTopRightRadius: 24,
            },
            tabBarLabelStyle: {
                fontSize: 12,
                fontWeight: '600',
            },
        }}>
      <Tabs.Screen name="index" options={{
            title: 'Trang chủ',
            tabBarIcon: ({ color, focused }) => (<View style={[styles.tabIcon, focused && styles.activeTabIcon]}><Ionicons name={focused ? 'home' : 'home-outline'} size={24} color={color}/></View>),
        }}/>
      <Tabs.Screen name="camera" options={{
            title: 'Chụp',
            tabBarStyle: { display: 'none' },
            tabBarIcon: ({ color, focused }) => (<View style={styles.cameraIconContainer}>
              <Ionicons name={focused ? 'scan-circle' : 'scan-circle-outline'} size={34} color={COLORS.primary}/>
            </View>),
        }} listeners={{
            tabPress: () => {
                logFlowDomain('ACQUIRE', 'HANDWRITING_TEXT');
            },
        }}/>
      <Tabs.Screen name="profile" options={{
            title: 'Của em',
            tabBarIcon: ({ color, focused }) => (<View style={[styles.tabIcon, focused && styles.activeTabIcon]}><Ionicons name={(focused ? 'person' : 'person-outline')} size={24} color={color}/></View>),
        }}/>
    </Tabs>);
}
const styles = StyleSheet.create({
    tabIcon: { width: 58, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
    activeTabIcon: { backgroundColor: COLORS.primaryLight },
    cameraIconContainer: {
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: -4,
    },
});
