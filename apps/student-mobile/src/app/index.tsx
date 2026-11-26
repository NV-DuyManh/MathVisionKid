import React, { useEffect, useContext } from 'react';
import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../constants/theme';
import { AuthContext } from '../context/AuthContext';
import { BrandLockup } from '../components/ui/BrandLockup';
import PortalScreen from '../features/portal/PortalScreen';

export default function SplashScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);

    useEffect(() => {
        if (auth?.isLoading) return;
        if (auth?.isAuthenticated) {
            router.replace('/(tabs)');
        }
    }, [router, auth?.isAuthenticated, auth?.isLoading]);

    if (auth?.isLoading) {
        return (
            <View style={styles.container}>
                <BrandLockup />
            </View>
        );
    }

    if (!auth?.isAuthenticated) {
        return <PortalScreen />;
    }

    return (
        <View style={styles.container}>
            <BrandLockup />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
        alignItems: 'center',
        justifyContent: 'center',
    },
});
