import React, { useEffect, useContext } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../constants/theme';
import { AuthContext } from '../context/AuthContext';
import { BrandLockup } from '../components/ui/BrandLockup';
import { hasCompletedOnboarding } from '../features/onboarding/onboardingStorage';
export default function SplashScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    useEffect(() => {
        if (auth?.isLoading) return;
        if (auth?.isAuthenticated) { router.replace('/(tabs)'); return; }
        if (Platform.OS === 'web') { router.replace('/login'); return; }
        let active = true;
        void hasCompletedOnboarding().then(completed => { if (active) router.replace(completed ? '/login' : '/welcome'); });
        return () => { active = false; };
    }, [router, auth?.isAuthenticated, auth?.isLoading]);
    return (<View style={styles.container}>
      <BrandLockup />
    </View>);
}
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
        alignItems: 'center',
        justifyContent: 'center',
    },

});
